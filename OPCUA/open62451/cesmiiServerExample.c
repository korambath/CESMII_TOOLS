#include <open62541/plugin/log_stdout.h>
#include <open62541/server.h>
#include <open62541/server_config_default.h>

#include <signal.h>
#include <stdlib.h>

/* Set a custom hostname in server configuration */
UA_DEPRECATED static UA_INLINE void
UA_ServerConfig_setCustomHostname(UA_ServerConfig *config,
                                  const UA_String customHostname) {
    UA_String_clear(&config->customHostname);
    UA_String_copy(&customHostname, &config->customHostname);
}

static volatile UA_Boolean running = true;
static void stopHandler(int sig) {
    UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "received ctrl-c");
    running = false;
}

UA_Double Temperature = 20.0;

static void
beforeReadTemperature(UA_Server *server,
               const UA_NodeId *sessionId, void *sessionContext,
               const UA_NodeId *nodeid, void *nodeContext,
               const UA_NumericRange *range, const UA_DataValue *data) {
    float max = 100.0;
    float min = 20.0;
    float tmp;
    tmp  = ((max - min) * ((float)rand() / RAND_MAX)) + min;
    Temperature = tmp;
    UA_Variant value;
    UA_Variant_setScalar(&value, &Temperature, &UA_TYPES[UA_TYPES_DOUBLE]); //Copy temperature in a variant variable
    //UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "Current Temperature Value called");
    UA_Server_writeValue(server, UA_NODEID_STRING(2, "C1_TS1_Temperature"), value);
}

static void
afterWriteState(UA_Server *server,
               const UA_NodeId *sessionId, void *sessionContext,
               const UA_NodeId *nodeId, void *nodeContext,
               const UA_NumericRange *range, const UA_DataValue *data) {
    UA_Variant value;
    UA_Boolean state;
    
    //state = false;
    UA_Server_readValue(server, UA_NODEID_STRING(2, "C1_CF1_State"), &value);

    state = *(UA_Boolean*) value.data;
 
    if (state == true){
        UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Furnace Door is OPEN");
    }
    else{
        UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Furnace Door is CLOSED");
    }
}


static void
usage(char **argv) {
    UA_LOG_WARNING(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND,
                   "Usage %s: [hostname portnumber]\n", argv[0]);
}


int main(int argc, char * argv[]) {
    signal(SIGINT, stopHandler);
    signal(SIGTERM, stopHandler);

    for(int i = 1; i < argc; i++) {
        if(strcmp(argv[i], "--help") == 0 ||
           strcmp(argv[i], "-h") == 0) {
            usage(argv);
            return EXIT_SUCCESS;
        }
    }

    if(argc < 2) {
        printf("Usage: %s ServerName [PortNumber (Default=4840)] \n",  argv[0]);
        return EXIT_FAILURE;
    }


    UA_Server *server = UA_Server_new();
 
    // check for arguments

    if (argc > 2 ) // hostname or ip address and a port number are available
    {
        for (int i = 0; i < argc; i++)
            printf("argv[%d] = %s\n", i, argv[i]);

        UA_Int16 port_number = atoi(argv[2]);
        UA_ServerConfig_setMinimal(UA_Server_getConfig(server), port_number, 0);
    }
    else
        UA_ServerConfig_setDefault(UA_Server_getConfig(server));
    if (argc > 1 )
    {   // hostname or ip address available
        // copy hostname from char * to an open62541 variable
        UA_String hostname;
        UA_String_init(&hostname);
        hostname.length = strlen(argv[1]);

        hostname.data = (UA_Byte *) argv[1];
        // change the configuration
        UA_ServerConfig_setCustomHostname(UA_Server_getConfig(server), hostname);
        
    }


    // Add a new namespace to the erver
    UA_Int16  ns_cesmii = UA_Server_addNamespace(server, "CESMII");
    UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "Name space addres with Nr %d", ns_cesmii);

    // Add a new object called Temperature sensor
    UA_NodeId c1_tempsens_Id;  /* get the nodeid assigned by the server */

    UA_ObjectAttributes oAttr = UA_ObjectAttributes_default;
    oAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Temperature Sensor");
    UA_Server_addObjectNode(server, UA_NODEID_STRING(2, "C1_TemperatureSensor"),
                            UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER),
                            UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES),
                            UA_QUALIFIEDNAME(2, "Temperature Sensor"), UA_NODEID_NUMERIC(0, UA_NS0ID_BASEOBJECTTYPE),
                            oAttr, NULL, &c1_tempsens_Id);

    // Add the variable manufacture name to server

    UA_VariableAttributes mnAttr = UA_VariableAttributes_default;
    UA_String manufacturerName = UA_STRING("CESMII Sensors Inc.");
    UA_Variant_setScalar(&mnAttr.value, &manufacturerName, &UA_TYPES[UA_TYPES_STRING]);
    mnAttr.displayName = UA_LOCALIZEDTEXT("en-US", "ManufacturerName");
    UA_Server_addVariableNode(server, UA_NODEID_STRING(2, "C1_TS1_ManufactureName"), c1_tempsens_Id,
                              UA_NODEID_NUMERIC(0, UA_NS0ID_HASCOMPONENT),
                              UA_QUALIFIEDNAME(2, "ManufacturerName"),
                              UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE), mnAttr, NULL, NULL);
 

    // Add the variable serial number  to server
    UA_VariableAttributes modelAttr = UA_VariableAttributes_default;
    UA_Int32 modelNumber = 3000;

    UA_Variant_setScalar(&modelAttr.value, &modelNumber, &UA_TYPES[UA_TYPES_INT32]);
    modelAttr.displayName = UA_LOCALIZEDTEXT("en-US", "ModelNumber");
    UA_Server_addVariableNode(server, UA_NODEID_STRING(2, "C1_TS1_ModelNumber"), c1_tempsens_Id,
                              UA_NODEID_NUMERIC(0, UA_NS0ID_HASCOMPONENT),
                              UA_QUALIFIEDNAME(2, "ModelNumber"),
                              UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE), modelAttr, NULL, NULL);
 
    // Add the variable Temperature to server
    UA_VariableAttributes tpAttr = UA_VariableAttributes_default;

    UA_Variant_setScalar(&tpAttr.value, &Temperature, &UA_TYPES[UA_TYPES_DOUBLE]);
    tpAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Temperature");
    UA_Server_addVariableNode(server, UA_NODEID_STRING(2, "C1_TS1_Temperature"), c1_tempsens_Id,
                              UA_NODEID_NUMERIC(0, UA_NS0ID_HASCOMPONENT),
                              UA_QUALIFIEDNAME(2, "Temperature"),
                              UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE), tpAttr, NULL, NULL);
 
    // Add a callback function

    //UA_NodeId currentNodeId = UA_NODEID_STRING(1, "current-time-value-callback");
    UA_ValueCallback callback ;
    callback.onRead = beforeReadTemperature;
    //callback.onWrite = afterWriteTime;
    callback.onWrite = NULL;
    UA_Server_setVariableNode_valueCallback(server, UA_NODEID_STRING(2, "C1_TS1_Temperature"), callback);


    // Add a new object called Furnace
    //UA_NodeId pumpId; /* get the nodeid assigned by the server */
    UA_NodeId c1_furnace_Id;

    UA_ObjectAttributes ofAttr = UA_ObjectAttributes_default;
    ofAttr.displayName = UA_LOCALIZEDTEXT("en-US", "CESMII Furnace");
    UA_Server_addObjectNode(server, UA_NODEID_STRING(2, "C1_Furnace"),
                            UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER),
                            UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES),
                            UA_QUALIFIEDNAME(2, "CESMII Furnace"), UA_NODEID_NUMERIC(0, UA_NS0ID_BASEOBJECTTYPE),
                            ofAttr, NULL, &c1_furnace_Id);

    // Add the variable manufacture name to server

    UA_VariableAttributes mnfAttr = UA_VariableAttributes_default;
    UA_String manufacturerName1 = UA_STRING("Cesmii Furnace Inc.");
    UA_Variant_setScalar(&mnfAttr.value, &manufacturerName1, &UA_TYPES[UA_TYPES_STRING]);
    mnfAttr.displayName = UA_LOCALIZEDTEXT("en-US", "ManufacturerName1");
    UA_Server_addVariableNode(server, UA_NODEID_STRING(2, "C1_CF1_ManufactureName"), c1_furnace_Id,
                              UA_NODEID_NUMERIC(0, UA_NS0ID_HASCOMPONENT),
                              UA_QUALIFIEDNAME(2, "ManufacturerName1"),
                              UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE), mnfAttr, NULL, NULL);


    // Add the variable model number  to server
    UA_VariableAttributes modelfAttr = UA_VariableAttributes_default;
    UA_Int32 modelNumber1 = 9000;

    UA_Variant_setScalar(&modelfAttr.value, &modelNumber1, &UA_TYPES[UA_TYPES_INT32]);
    modelfAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Furnace ModelNumber");
    UA_Server_addVariableNode(server, UA_NODEID_STRING(2, "C1_CF1_ModelNumber"), c1_furnace_Id,
                              UA_NODEID_NUMERIC(0, UA_NS0ID_HASCOMPONENT),
                              UA_QUALIFIEDNAME(2, "Furnace ModelNumber"),
                              UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE), modelfAttr, NULL, NULL);


    // Add the variable state to the Furnace (Door open or close) 
    UA_VariableAttributes stateAttr = UA_VariableAttributes_default;
    UA_Boolean state = false;
    //UA_Boolean state = true;

    UA_Variant_setScalar(&stateAttr.value, &state, &UA_TYPES[UA_TYPES_BOOLEAN]);
    stateAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;

    stateAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Furnace Door State");
    UA_Server_addVariableNode(server, UA_NODEID_STRING(2, "C1_CF1_State"), c1_furnace_Id,
                              UA_NODEID_NUMERIC(0, UA_NS0ID_HASCOMPONENT),
                              UA_QUALIFIEDNAME(2, "Furnace Door State"),
                              UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE), stateAttr, NULL, NULL);


    // Add call back to the state of furnace door
    UA_ValueCallback callback1 ;
    callback1.onRead = NULL;
    callback1.onWrite = afterWriteState;
    UA_Server_setVariableNode_valueCallback(server, UA_NODEID_STRING(2, "C1_CF1_State"), callback1);



    UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "starting server ....");
    UA_StatusCode retval = UA_Server_run(server, &running);
    UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "Server was shutdown ....");
    


    UA_Server_delete(server);
    return retval == UA_STATUSCODE_GOOD ? EXIT_SUCCESS : EXIT_FAILURE;
}

