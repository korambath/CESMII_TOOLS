
import dotenv from "dotenv";
import os from "node:os";
import path from "node:path";
import Anthropic from "@anthropic-ai/sdk";
import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";

import { betaZodTool } from "@anthropic-ai/sdk/helpers/beta/zod";
import { z } from "zod";

// --------------------------------------------------
// 1. Load environment variables
// --------------------------------------------------

dotenv.config({
  path: path.join(os.homedir(), ".config", ".env"),
});

// Initialize Anthropic client
const client = new Anthropic();

// Automatically detect the timezone of the machine running Node.js
const serverTimeZone =
  Intl.DateTimeFormat().resolvedOptions().timeZone;

console.log(`\nServer timezone detected: ${serverTimeZone}`);

// User's preferred timezone (set at startup, read by the tools)
let preferredTimeZone = serverTimeZone;

// Abort any HTTP request that takes longer than this
const FETCH_TIMEOUT_MS = 15000;

// --------------------------------------------------
// 2. Geocoding function
// --------------------------------------------------

async function getCoordinates(location: string) {
  const geoUrl = new URL(
    "https://nominatim.openstreetmap.org/search"
  );

  geoUrl.searchParams.set("q", location);
  geoUrl.searchParams.set("format", "json");
  geoUrl.searchParams.set("limit", "1");

  const response = await fetch(geoUrl, {
    headers: {
      "User-Agent": "weather_finder/1.0",
    },
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  });

  if (!response.ok) {
    throw new Error("Geocoding service unavailable");
  }

  const data = await response.json();

  if (!Array.isArray(data) || data.length === 0) {
    return null;
  }

  return {
    latitude: Number(data[0].lat),
    longitude: Number(data[0].lon),
  };
}

// --------------------------------------------------
// 3. Get current weather
// --------------------------------------------------

async function getWeather( location: string, preferredTimeZone: string): Promise<object> {
  try {
    // Get coordinates
    const coordinates = await getCoordinates(location);

    if (!coordinates) {
      return { error: `City not found: ${location}` };
    }

    const { latitude, longitude } = coordinates;

    // Open-Meteo API
    const weatherUrl = new URL(
      "https://api.open-meteo.com/v1/forecast"
    );

    weatherUrl.searchParams.set("timezone", "auto");
    weatherUrl.searchParams.set("latitude", String(latitude));
    weatherUrl.searchParams.set("longitude", String(longitude));

    weatherUrl.searchParams.set(
      "current",
      "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
    );

    weatherUrl.searchParams.set("temperature_unit", "fahrenheit");
    weatherUrl.searchParams.set("wind_speed_unit", "mph");

    const response = await fetch(weatherUrl, {
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    });

    if (!response.ok) {
      throw new Error("Weather API request failed");
    }

    const data = await response.json();

    if (!data.current) {
      return { error: "Weather data unavailable" };
    }

    const current = data.current;
    // Capture the current instant once
    const now = new Date();

    return {
      location,
      latitude,
      longitude,

      // Timezone information
      city_timezone: data.timezone,
      city_timezone_abbreviation: data.timezone_abbreviation,
      server_timezone: serverTimeZone,
      preferred_timezone: preferredTimeZone,

      // Actual current time, formatted independently
      city_current_time: new Intl.DateTimeFormat("en-US", {
        dateStyle: "full",
        timeStyle: "long",
        timeZone: data.timezone,
      }).format(now),

      preferred_current_time: new Intl.DateTimeFormat("en-US", {
        dateStyle: "full",
        timeStyle: "long",
        timeZone: preferredTimeZone,
      }).format(now),

      server_current_time: new Intl.DateTimeFormat("en-US", {
        dateStyle: "full",
        timeStyle: "long",
        timeZone: serverTimeZone,
      }).format(now),

      // Keep this separately as the observation timestamp
      weather_observation_time: current.time,

      // Actual weather
      temperature_f: current.temperature_2m,
      humidity_percent: current.relative_humidity_2m,
      precipitation_mm: current.precipitation,
      wind_speed_mph: current.wind_speed_10m,
    };

  } catch (error) {
    console.error("Weather error:", error);

    return {
      error:
        error instanceof Error
          ? error.message
          : "Unable to retrieve weather data",
    };
  } 
}

// --------------------------------------------------
// 4. Get weather forecast for the next 3 days
// --------------------------------------------------

async function getForecast( location: string, preferredTimeZone: string): Promise<object>{
  try {
    // Get coordinates
    const coordinates = await getCoordinates(location);

    if (!coordinates) {
      return { error: `City not found: ${location}` };
    }

    const { latitude, longitude } = coordinates;

    // Open-Meteo forecast API
    const forecastUrl = new URL(
      "https://api.open-meteo.com/v1/forecast"
    );

    forecastUrl.searchParams.set("timezone", "auto");
    forecastUrl.searchParams.set("latitude", String(latitude));
    forecastUrl.searchParams.set("longitude", String(longitude));

    // Daily forecast parameters
    forecastUrl.searchParams.set(
      "daily",
      [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "precipitation_probability_max",
        "wind_speed_10m_max",
        "weather_code",
      ].join(",")
    );

    forecastUrl.searchParams.set("temperature_unit", "fahrenheit");
    forecastUrl.searchParams.set("wind_speed_unit", "mph");
    forecastUrl.searchParams.set("forecast_days", "3");

    const response = await fetch(forecastUrl, {
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    });

    if (!response.ok) {
      throw new Error("Forecast API request failed");
    }

    const data = await response.json();

    if (!data.daily) {
      return { error: "Forecast data unavailable" };
    }

    const daily = data.daily;

    // Convert each date into a reliable weekday name
    const forecast = daily.time.map(
      (date: string, index: number) => {
        // Use UTC to calculate the calendar weekday
        // without depending on the computer's timezone.
        const dateObject = new Date(`${date}T12:00:00Z`);

        const dayOfWeek = new Intl.DateTimeFormat("en-US", {
          weekday: "long",
          timeZone: "UTC",
        }).format(dateObject);

        return {
          date,
          day_of_week: dayOfWeek,
          temperature_max_f: daily.temperature_2m_max[index],
          temperature_min_f: daily.temperature_2m_min[index],
          precipitation_mm: daily.precipitation_sum[index],
          precipitation_probability_percent:
            daily.precipitation_probability_max[index],
          wind_speed_max_mph: daily.wind_speed_10m_max[index],
          weather_code: daily.weather_code[index],
        };
      }
    );

   return {
     location,
     latitude,
     longitude,

     city_timezone: data.timezone,
     city_timezone_abbreviation: data.timezone_abbreviation,

     server_timezone: serverTimeZone,
     preferred_timezone: preferredTimeZone,

     forecast,
   };

  } catch (error) {
    console.error("Forecast error:", error);

    return {
      error:
        error instanceof Error
          ? error.message
          : "Unable to retrieve forecast",
    };
  }
}


// --------------------------------------------------
// 5. Get local time for any city
// --------------------------------------------------

async function getTimeOfDay(
  location: string,
  preferredTimeZone: string
): Promise<object> {
  try {
    // Resolve city coordinates
    const coordinates = await getCoordinates(location);

    if (!coordinates) {
      return { error: `City not found: ${location}` };
    }

    const { latitude, longitude } = coordinates;

    // Ask Open-Meteo for the city's timezone
    const url = new URL(
      "https://api.open-meteo.com/v1/forecast"
    );

    url.searchParams.set("latitude", String(latitude));
    url.searchParams.set("longitude", String(longitude));
    url.searchParams.set("current", "temperature_2m");
    url.searchParams.set("timezone", "auto");

    const response = await fetch(url, {
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    });

    if (!response.ok) {
      throw new Error("Unable to retrieve city timezone");
    }

    const data = await response.json();

    if (!data.timezone) {
      return { error: "City timezone unavailable" };
    }

    // Capture one exact current instant
    const now = new Date();

    // Format time in the requested city's timezone
    const cityTime = new Intl.DateTimeFormat("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
      timeZone: data.timezone,
      timeZoneName: "long",
    }).format(now);

    // Format time in user's preferred timezone
    const userTime = new Intl.DateTimeFormat("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
      timeZone: preferredTimeZone,
      timeZoneName: "long",
    }).format(now);

    // Determine time of day in the requested city
    const cityHour = Number(
      new Intl.DateTimeFormat("en-US", {
        hour: "2-digit",
        hourCycle: "h23",
        timeZone: data.timezone,
      }).format(now)
    );

    let timeOfDay: string;

    if (cityHour >= 5 && cityHour < 12) {
      timeOfDay = "Morning";
    } else if (cityHour >= 12 && cityHour < 17) {
      timeOfDay = "Afternoon";
    } else if (cityHour >= 17 && cityHour < 21) {
      timeOfDay = "Evening";
    } else {
      timeOfDay = "Night";
    }

    return {
      location,
      latitude,
      longitude,

      city_timezone: data.timezone,
      city_time: cityTime,
      preferred_timezone: preferredTimeZone,
      preferred_time: userTime,

      time_of_day: timeOfDay,
      hour_24: cityHour,

      timestamp_utc: now.toISOString(),
    };

  } catch (error) {
    console.error("Time error:", error);

    return {
      error:
        error instanceof Error
          ? error.message
          : "Unable to retrieve local time",
    };
  }
}


// --------------------------------------------------
// 6. Get weather alerts for the next 3 days
// --------------------------------------------------
//
// Open-Meteo has no official warnings feed, so these alerts are
// derived from its daily forecast using common thresholds
// (roughly following US National Weather Service criteria).

type WeatherAlert = {
  level: "advisory" | "warning";
  event: string;
  detail: string;
};

// Return the alerts triggered by one day of the daily forecast
function checkDayForAlerts(daily: any, i: number): WeatherAlert[] {
  const alerts: WeatherAlert[] = [];

  const add = (level: WeatherAlert["level"], event: string, detail: string) => {
    alerts.push({ level, event, detail });
  };

  const code: number = daily.weather_code[i];
  const rainMm: number = daily.precipitation_sum[i] ?? 0;
  const snowCm: number = daily.snowfall_sum[i] ?? 0;
  const gustsMph: number = daily.wind_gusts_10m_max[i] ?? 0;
  const feelsMaxF: number | null = daily.apparent_temperature_max[i];
  const feelsMinF: number | null = daily.apparent_temperature_min[i];
  const uv: number = daily.uv_index_max[i] ?? 0;

  // Severe weather from the WMO weather code
  if (code === 96 || code === 99) {
    add("warning", "Thunderstorm with hail", `Weather code ${code}`);
  } else if (code === 95) {
    add("warning", "Thunderstorm", "Weather code 95");
  }
  if ([56, 57, 66, 67].includes(code)) {
    add("warning", "Freezing rain or drizzle", `Weather code ${code}`);
  }
  if (code === 45 || code === 48) {
    add("advisory", code === 48 ? "Freezing fog" : "Fog", `Weather code ${code}`);
  }

  // Rain
  if (rainMm >= 50) {
    add("warning", "Heavy rain", `${rainMm} mm expected`);
  } else if (rainMm >= 25 || code === 65 || code === 82) {
    add("advisory", "Heavy rain", `${rainMm} mm expected`);
  }

  // Snow
  if (snowCm >= 15) {
    add("warning", "Heavy snow", `${snowCm} cm expected`);
  } else if (snowCm >= 5) {
    add("advisory", "Snow", `${snowCm} cm expected`);
  }

  // Wind
  if (gustsMph >= 58) {
    add("warning", "High wind", `Gusts up to ${gustsMph} mph`);
  } else if (gustsMph >= 45) {
    add("advisory", "Wind", `Gusts up to ${gustsMph} mph`);
  }

  // Heat and cold (using the "feels like" temperature)
  if (feelsMaxF != null && feelsMaxF >= 105) {
    add("warning", "Extreme heat", `Feels like up to ${feelsMaxF}°F`);
  } else if (feelsMaxF != null && feelsMaxF >= 100) {
    add("advisory", "Heat", `Feels like up to ${feelsMaxF}°F`);
  }
  if (feelsMinF != null && feelsMinF <= -15) {
    add("warning", "Extreme cold", `Feels like down to ${feelsMinF}°F`);
  } else if (feelsMinF != null && feelsMinF <= 0) {
    add("advisory", "Cold", `Feels like down to ${feelsMinF}°F`);
  }

  // UV
  if (uv >= 11) {
    add("warning", "Extreme UV", `UV index ${uv}`);
  } else if (uv >= 8) {
    add("advisory", "Very high UV", `UV index ${uv}`);
  }

  return alerts;
}

async function getAlerts(location: string, preferredTimeZone: string): Promise<object> {
  try {
    // Get coordinates
    const coordinates = await getCoordinates(location);

    if (!coordinates) {
      return { error: `City not found: ${location}` };
    }

    const { latitude, longitude } = coordinates;

    // Open-Meteo forecast API, asking only for the fields
    // the alert checks need
    const alertsUrl = new URL(
      "https://api.open-meteo.com/v1/forecast"
    );

    alertsUrl.searchParams.set("timezone", "auto");
    alertsUrl.searchParams.set("latitude", String(latitude));
    alertsUrl.searchParams.set("longitude", String(longitude));

    alertsUrl.searchParams.set(
      "daily",
      [
        "weather_code",
        "precipitation_sum",
        "snowfall_sum",
        "wind_gusts_10m_max",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "uv_index_max",
      ].join(",")
    );

    alertsUrl.searchParams.set("temperature_unit", "fahrenheit");
    alertsUrl.searchParams.set("wind_speed_unit", "mph");
    alertsUrl.searchParams.set("forecast_days", "3");

    const response = await fetch(alertsUrl, {
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    });

    if (!response.ok) {
      throw new Error("Alerts API request failed");
    }

    const data = await response.json();

    if (!data.daily) {
      return { error: "Forecast data for alerts unavailable" };
    }

    const daily = data.daily;

    const days = daily.time.map((date: string, index: number) => {
      // Use UTC to calculate the calendar weekday
      // without depending on the computer's timezone.
      const dayOfWeek = new Intl.DateTimeFormat("en-US", {
        weekday: "long",
        timeZone: "UTC",
      }).format(new Date(`${date}T12:00:00Z`));

      return {
        date,
        day_of_week: dayOfWeek,
        alerts: checkDayForAlerts(daily, index),
      };
    });

    return {
      location,
      latitude,
      longitude,

      city_timezone: data.timezone,
      preferred_timezone: preferredTimeZone,

      source: "Derived from the Open-Meteo forecast; not official government warnings",
      alert_count: days.reduce(
        (total: number, day: { alerts: WeatherAlert[] }) => total + day.alerts.length,
        0
      ),
      days,
    };

  } catch (error) {
    console.error("Alerts error:", error);

    return {
      error:
        error instanceof Error
          ? error.message
          : "Unable to retrieve weather alerts",
    };
  }
}


// --------------------------------------------------
// 7. Define Claude tools using Zod
// --------------------------------------------------


const weatherTool = betaZodTool({
  name: "get_weather",

  description:
    "Get today's actual current weather for a city.",

  inputSchema: z.object({
    city: z.string().describe("The city to check"),
  }),

  run: async ({ city }) => {
    console.log(`\nFetching current weather for ${city}...`);

    const result = await getWeather(city, preferredTimeZone);

    return JSON.stringify(result, null, 2);
  },
});

const forecastTool = betaZodTool({
  name: "get_forecast",

  description:
    "Get the weather forecast for the next three days for a city.",

  inputSchema: z.object({
    city: z.string().describe("The city to check"),
  }),

  run: async ({ city }) => {
    console.log(`\nFetching 3-day forecast for ${city}...`);

    const result = await getForecast(city, preferredTimeZone);

    return JSON.stringify(result, null, 2);
  },
});


const timeTool = betaZodTool({
  name: "get_time_of_day",

  description:
    "Get the actual current local time, date, timezone, and time of day (morning, afternoon, evening, or night) for any city. Also compare it with the user's preferred timezone.",

  inputSchema: z.object({
    city: z.string().describe("The city to check the local time for"),
  }),

  run: async ({ city }) => {
    console.log(`\nFetching local time for ${city}...`);

    const result = await getTimeOfDay(
      city,
      preferredTimeZone
    );

    return JSON.stringify(result, null, 2);
  },
});


const alertsTool = betaZodTool({
  name: "get_weather_alerts",

  description:
    "Check the next three days for severe weather in a city (thunderstorms, hail, freezing rain, fog, heavy rain or snow, high wind, extreme heat or cold, very high UV). Alerts are derived from the forecast, not official government warnings.",

  inputSchema: z.object({
    city: z.string().describe("The city to check for weather alerts"),
  }),

  run: async ({ city }) => {
    console.log(`\nChecking weather alerts for ${city}...`);

    const result = await getAlerts(city, preferredTimeZone);

    return JSON.stringify(result, null, 2);
  },
});



// --------------------------------------------------
// 8. Initialize terminal input
// --------------------------------------------------

const rl = readline.createInterface({
  input,
  output,
});

// --------------------------------------------------
// 9. Interactive weather assistant
// --------------------------------------------------

console.log("======================================");
console.log("       WEATHER AI ASSISTANT");
console.log("======================================");
console.log("Ask about current weather or forecasts.");
console.log("Type 'quit' or 'exit' to stop.");
console.log("======================================");

const timezoneInput = await rl.question(
  `\nYour server timezone is ${serverTimeZone}. ` +
  `Enter your preferred timezone (or press Enter to use this): `
);

if (timezoneInput.trim()) {
  try {
    new Intl.DateTimeFormat("en-US", {
      timeZone: timezoneInput.trim(),
    });

    preferredTimeZone = timezoneInput.trim();

  } catch {
    console.log("Invalid timezone. Using server timezone.");
  }
}

console.log(`Using timezone: ${preferredTimeZone}`);

// Standing instructions for Claude (sent as the system prompt
// so they don't repeat in the conversation history)
const systemPrompt = `
You are a weather assistant.

Available tools:

1. get_weather:
   Retrieves actual current weather.

2. get_forecast:
   Retrieves the next three days of weather.

3. get_time_of_day:
   Retrieves the actual local time and date
   for a city.

4. get_weather_alerts:
   Checks the next three days for severe weather.

TIMEZONE INFORMATION:
- Server timezone: ${serverTimeZone}
- Preferred timezone: ${preferredTimeZone}

TIMEZONE RULES:
- city_current_time is the actual current time in the
  requested city's timezone.
- preferred_current_time is the actual current time
  in the user's preferred timezone.
- Both timestamps represent the exact same instant.
- Never use weather_observation_time as the current clock time.
- weather_observation_time is only the timestamp
  associated with the weather observation.
- Never independently calculate or guess the time.
- Display the exact timestamps returned by the tools.

INSTRUCTIONS:

- If the user asks about weather, use get_weather.
- If the user asks about a forecast, use get_forecast.
- If the user asks about local time, use get_time_of_day.
- If the user asks about alerts, warnings, or severe weather,
  use get_weather_alerts.
- When you report alerts, say they are derived from the
  forecast and are not official warnings. Point the user to
  their local weather service for official warnings.
- If the user asks about both weather and time,
  use the appropriate tools.
- If the user asks for a time comparison,
  use get_time_of_day for the requested cities.
- If a follow-up question doesn't name a city, use the
  city from earlier in the conversation.
- Always use the timezone information returned
  by the tools.
- Never guess the current time or date.
- Never confuse weather observation time
  with the actual current time.
- Never invent weather information.

CLOTHING RECOMMENDATIONS:
- Recommend appropriate clothing for today.
- Identify rainy or unusually windy days.
- Recommend what to pack for the next three days.


Provide clear, conversational answers.
If a tool returns an error, explain it clearly.
Never invent weather information.
`;

// Conversation history, kept across questions so follow-ups
// like "what about tomorrow?" know which city was meant
const history: Anthropic.Beta.Messages.BetaMessageParam[] = [];

// Interactive loop
while (true) {


  // Ask user for a city

  const city = await rl.question(
    "\nWhat would you like to know? (e.g. Weather in LA, forecast for NYC, or time in Tokyo): "
  );

  const location = city.trim();

  // Exit condition
  if (
    location.toLowerCase() === "quit" ||
    location.toLowerCase() === "exit"
  ) {
    console.log("\nGoodbye! Thanks for using Weather AI.");
    break;
  }

  // Validate input
  if (!location) {
    console.log("Please enter a valid city name.");
    continue;
  }

  history.push({ role: "user", content: location });

  try {

    // --------------------------------------------------
    // 10. Run Claude with automatic tool execution
    // --------------------------------------------------

    const runner = client.beta.messages.toolRunner({
      model: "claude-opus-5-5",

      // Thinking counts toward max_tokens, so leave plenty of room
      max_tokens: 16000,

      // "summarized" returns a readable summary of Claude's reasoning
      // (the default, "omitted", returns empty thinking text)
      thinking: { type: "adaptive", display: "summarized" },

      // low | medium | high | xhigh | max (Opus 5.5 defaults to medium)
      output_config: { effort: "medium" },

      // If a safety classifier declines the request, let the API
      // retry it on a fallback model instead of stopping
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",

      system: systemPrompt,

      // Pass a copy so the runner can't modify our history
      messages: [...history],

      tools: [
        weatherTool,
        forecastTool,
        timeTool,
        alertsTool,
      ],
    });

    // Step through each round of the conversation (Claude may call
    // tools several times), show its reasoning as it goes, and
    // record every round exactly as it was sent
    let finalMessage: Anthropic.Beta.Messages.BetaMessage | undefined;
    const turn: Anthropic.Beta.Messages.BetaMessageParam[] = [];

    for await (const message of runner) {
      for (const block of message.content) {
        if (block.type === "thinking" && block.thinking) {
          console.log(`\n[Thinking] ${block.thinking}`);
        }
      }
      finalMessage = message;

      // Claude's message, unchanged (thinking and tool calls included)
      turn.push({ role: "assistant", content: message.content });

      // The tool results the runner sends back next. The runner
      // caches them, so this doesn't run any tool twice.
      const toolResults = await runner.generateToolResponse();
      if (toolResults) {
        turn.push(toolResults);
      }
    }

    if (!finalMessage || finalMessage.stop_reason === "refusal") {
      history.pop();
      console.log("\nClaude declined to answer that request.");
      continue;
    }

    // Keep the whole exchange for follow-up questions. Thinking
    // blocks are only valid alongside the exact conversation that
    // produced them, so the history is only ever appended to.
    history.push(...turn);

    // --------------------------------------------------
    // 11. Display Claude's final response
    // --------------------------------------------------

    console.log("\n======================================");
    console.log("         WEATHER ASSISTANT");
    console.log("======================================");

    for (const block of finalMessage.content) {
      if (block.type === "text") {
        console.log(block.text);
      }
    }

    console.log("\n======================================");

  } catch (error) {
    // Drop the unanswered question so the history stays valid
    history.pop();

    console.error("\nAn error occurred:", error);
    console.log("Please try again with another city.");
  }
}

// --------------------------------------------------
// 12. Close terminal
// --------------------------------------------------

rl.close();
