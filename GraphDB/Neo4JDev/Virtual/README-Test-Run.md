
# To delete everything before
MATCH (n)
DETACH DELETE n


1. Example 1:

CREATE (friend:Person)-[:WROTE]->(message:IG)-[:TALKING_ABOUT]->(weburl:Website)
SET friend.name ="Cesmii",
    message.text= "hey checkout this website",
    weburl.name = "cesmii.org"
RETURN friend, message, weburl


2. Example 2:
CREATE (sensor:Sensor)-[:DETECTED]->(event:Anomaly)-[:AFFECTS]->(machine:Machine)
SET sensor.id = "Sensor-42",
    event.type = "Temperature Spike",
    machine.name = "Assembly Robot A3"
RETURN sensor, event, machine

A Brief Explanation for Example 2.

Node Label: :Sensor,A device that monitors a manufacturing process 
Relationship: -[:DETECTED]->,The action of the sensor reporting a reading or event.
Node Label: :Anomaly,"The data/event that was generated, representing an unexpected reading or deviation ."
Relationship: -[:AFFECTS]->,The connection between the detected event and the physical asset it impacts.
Node Label: :Machine,The physical asset or production system that is the subject of the event .
Property: sensor.id,A unique identifier for the sensor.
Property: event.type,The type of event that occurred.
Property: machine.name,The identifier of the machine/asset.

3. Example 3:
CREATE (doctor:Physician)-[:PRESCRIBED]->(drug:Medication)-[:TREATS]->(condition:Diagnosis)
SET doctor.name = "Dr. Smith",
    drug.name = "Lipitor",
    condition.name = "Hypercholesterolemia"
RETURN doctor, drug, condition



CREATE (:Person:Actor {name: 'Tom Hanks', born: 1956})-[:ACTED_IN {roles: ['Forrest']}]->(:Movie {title: 'Forrest Gump', released: 1994})<-[:DIRECTED]-(:Person {name: 'Robert Zemeckis', born: 1951})

MATCH (a:Person:Actor {name: 'Tom Hanks', born: 1956})
      -[:ACTED_IN {roles: ['Forrest']}]->(m:Movie {title: 'Forrest Gump', released: 1994})
      <-[:DIRECTED]-(d:Person {name: 'Robert Zemeckis', born: 1951})
RETURN a, m, d


MATCH (actor:Person {name: 'Tom Hanks'})
      -[:ACTED_IN]->(movie:Movie {title: 'Forrest Gump'})
      <-[:DIRECTED]-(director:Person {name: 'Robert Zemeckis'})
RETURN actor, movie, director

MATCH (actor)-[r:ACTED_IN]->(movie:Movie {title: 'Forrest Gump'})
      <-[:DIRECTED]-(director)
RETURN actor.name, r.roles, director.name, movie.released


