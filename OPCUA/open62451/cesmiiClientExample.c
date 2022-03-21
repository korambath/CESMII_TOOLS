#include <open62541/client_config_default.h>
#include <open62541/client_highlevel.h>
#include <open62541/plugin/log_stdout.h>

#include <stdlib.h>


static UA_StatusCode
nodeIter(UA_NodeId childId, UA_Boolean isInverse, UA_NodeId referenceTypeId, void *handle) {
    if(isInverse)
        return UA_STATUSCODE_GOOD;
    UA_NodeId *parent = (UA_NodeId *)handle;
    printf("%d, %d --- %d ---> NodeId %d, %d\n",
           parent->namespaceIndex, parent->identifier.numeric,
           referenceTypeId.identifier.numeric, childId.namespaceIndex,
           childId.identifier.numeric);
    if(childId.identifierType == UA_NODEIDTYPE_STRING) {
       printf("%d, %d --- %d ---> NodeId %d, %d , %.*s\n",
           parent->namespaceIndex, parent->identifier.numeric,
           referenceTypeId.identifier.numeric, childId.namespaceIndex,
           childId.identifier.numeric, (int) childId.identifier.string.length, childId.identifier.string.data);

    }
    return UA_STATUSCODE_GOOD;
}

void browsobject(UA_BrowseResponse bResp)
{
    for(size_t i = 0; i < bResp.resultsSize; ++i)
    {
        for(size_t j = 0; j < bResp.results[i].referencesSize; ++j)
        {
            UA_ReferenceDescription *ref = &(bResp.results[i].references[j]);
            if(ref->nodeId.nodeId.identifierType == UA_NODEIDTYPE_NUMERIC)
            {
                printf("%-9d %-24d %-24.*s %-24.*s\n", ref->browseName.namespaceIndex,
                //printf("%-9d %-16d %-16.*s %-16.*s\n", ref->nodeId.nodeId.namespaceIndex,
                       ref->nodeId.nodeId.identifier.numeric, (int)ref->browseName.name.length,
                       ref->browseName.name.data, (int)ref->displayName.text.length,
                       ref->displayName.text.data);
            }
            else if(ref->nodeId.nodeId.identifierType == UA_NODEIDTYPE_STRING)
            {
                printf("%-9d %-24.*s %-24.*s %-24.*s\n", ref->browseName.namespaceIndex,
                //printf("%-9d %-16.*s %-16.*s %-16.*s\n", ref->nodeId.nodeId.namespaceIndex,
                       (int)ref->nodeId.nodeId.identifier.string.length,
                       ref->nodeId.nodeId.identifier.string.data,
                       (int)ref->browseName.name.length, ref->browseName.name.data,
                       (int)ref->displayName.text.length, ref->displayName.text.data);
            }
            /* TODO: distinguish further types */
        }
    }
}



int main(void) {
    UA_Client *client = UA_Client_new();
    UA_ClientConfig_setDefault(UA_Client_getConfig(client));
    UA_StatusCode retval = UA_Client_connect(client, "opc.tcp://localhost:4840");
    if(retval != UA_STATUSCODE_GOOD) {
        UA_Client_delete(client);
        return (int)retval;
    }

    /* Read the value attribute of the node. UA_Client_readValueAttribute is a
     * wrapper for the raw read service available as UA_Client_Service_read. */
    UA_Variant value; /* Variants can hold scalar values and arrays of any type */
    UA_Variant_init(&value);

    /* NodeId of the variable holding the current time */
    const UA_NodeId nodeId = UA_NODEID_NUMERIC(0, UA_NS0ID_SERVER_SERVERSTATUS_CURRENTTIME);
    retval = UA_Client_readValueAttribute(client, nodeId, &value);

    if(retval == UA_STATUSCODE_GOOD &&
       UA_Variant_hasScalarType(&value, &UA_TYPES[UA_TYPES_DATETIME])) {
        UA_DateTime raw_date = *(UA_DateTime *) value.data;
        UA_DateTimeStruct dts = UA_DateTime_toStruct(raw_date);
        UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "date is: %u-%u-%u %u:%u:%u.%03u\n",
                    dts.day, dts.month, dts.year, dts.hour, dts.min, dts.sec, dts.milliSec);
    }

    // Browse some objects
    printf("Browsing nodes in objects folder:\n");

    UA_BrowseRequest bReq;
    UA_BrowseRequest_init(&bReq);
    bReq.requestedMaxReferencesPerNode = 0;
    bReq.nodesToBrowse = UA_BrowseDescription_new();
    bReq.nodesToBrowseSize = 1;
    bReq.nodesToBrowse[0].nodeId = UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER); //browse objects folder
    bReq.nodesToBrowse[0].resultMask = UA_BROWSERESULTMASK_ALL; //return everything

    UA_BrowseResponse bResp = UA_Client_Service_browse(client, bReq);
    printf("%-9s %-24s %-24s %-24s\n", "NAMESPACE", "NODEID", "BROWSE NAME", "DISPLAY NAME");
    browsobject(bResp);

    UA_BrowseRequest bReq2;
    UA_BrowseRequest_init(&bReq2);
    bReq2.requestedMaxReferencesPerNode = 0;
    bReq2.nodesToBrowse = UA_BrowseDescription_new();
    bReq2.nodesToBrowseSize = 1;
    //bReq2.nodesToBrowse[0].nodeId = UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER); //browse objects folder
    bReq2.nodesToBrowse[0].resultMask = UA_BROWSERESULTMASK_ALL; //return everything
    printf("%-9s %-24s %-24s %-24s\n", "NAMESPACE", "NODEID", "BROWSE NAME", "DISPLAY NAME");

    // Why we are using UA_NODEID_STRING_ALLOC ?
    // UA_NODEID_STRING_ALLOC will use malloc to create a copy of the string.
    // UA_NODEID_STRING will add a reference to the passed string, it will not create a copy.
    // Since UA_BrowseRequest_deleteMembers(&bReq); is trying to delete all of its content, 
    // including the nodeId, it will try to free the string the.answer but it is on the stack, not heap.

    bReq2.nodesToBrowse[0].nodeId = UA_NODEID_STRING_ALLOC(2, "C1_TemperatureSensor"); //browse objects folder
    UA_BrowseResponse bResp2 = UA_Client_Service_browse(client, bReq2);
    browsobject(bResp2);

    printf("%-9s %-24s %-24s %-24s\n", "NAMESPACE", "NODEID", "BROWSE NAME", "DISPLAY NAME");
    bReq2.nodesToBrowse[0].nodeId = UA_NODEID_STRING_ALLOC(2, "C1_Furnace"); //browse objects folder
    bResp2 = UA_Client_Service_browse(client, bReq2);
    browsobject(bResp2);

    UA_BrowseRequest_clear(&bReq);
    UA_BrowseResponse_clear(&bResp);
    UA_BrowseRequest_clear(&bReq2);
    UA_BrowseResponse_clear(&bResp2);

    //UA_BrowseRequest_deleteMembers(&bReq);
    //UA_BrowseResponse_deleteMembers(&bResp);

    /* Same thing, this time using the node iterator... */
    UA_NodeId *parent = UA_NodeId_new();
    *parent = UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER);
    UA_Client_forEachChildNodeCall(client, UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER), nodeIter, (void *) parent);

    *parent = UA_NODEID_STRING_ALLOC(2, "C1_TemperatureSensor"); 
    UA_Client_forEachChildNodeCall(client, UA_NODEID_STRING_ALLOC(2, "C1_TemperatureSensor"), nodeIter, (void *) parent);

    *parent = UA_NODEID_STRING_ALLOC(2, "C1_Furnace");
    UA_Client_forEachChildNodeCall(client, UA_NODEID_STRING_ALLOC(2, "C1_Furnace"), nodeIter, (void *) parent);

    UA_NodeId_delete(parent);


    //Variables for read access
    UA_String ManufactureName;
    UA_Int32 ModelNumber;
    UA_Double Temperature;

    //Read Temperature sensor Manufacturer Name
    retval = UA_Client_readValueAttribute(client, UA_NODEID_STRING(2, "C1_TS1_ManufactureName"), &value);
    if(retval == UA_STATUSCODE_GOOD && UA_Variant_hasScalarType(&value, &UA_TYPES[UA_TYPES_STRING])) {
       ManufactureName =  *(UA_String *) value.data;
       UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Sensor Manufacturer is %.*s", (int)ManufactureName.length, ManufactureName.data);
    }

    //Read the Temperature sensor Model Number
    retval = UA_Client_readValueAttribute(client, UA_NODEID_STRING(2, "C1_TS1_ModelNumber"), &value);
    if(retval == UA_STATUSCODE_GOOD && UA_Variant_hasScalarType(&value, &UA_TYPES[UA_TYPES_INT32])) {
	ModelNumber = *(UA_Int32 *) value.data;
        UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Sensor Model Number is %d", ModelNumber);
    }

    //Read the Temperature

    for ( size_t i = 1; i < 3; ++i) {
        retval = UA_Client_readValueAttribute(client, UA_NODEID_STRING(2, "C1_TS1_Temperature"), &value);
        if(retval == UA_STATUSCODE_GOOD && UA_Variant_hasScalarType(&value, &UA_TYPES[UA_TYPES_DOUBLE])) {
	    Temperature = *(UA_Double *) value.data;
            UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Temperature %zu is %f", i, Temperature);
        }
    }

    // declare variables for the furnace object
    UA_String ManufactureName2;
    UA_Int32 ModelNumber2;
    UA_Boolean state;          

    // Read the furnace manufacturer	

    retval = UA_Client_readValueAttribute(client, UA_NODEID_STRING(2, "C1_CF1_ManufactureName"), &value);
    if(retval == UA_STATUSCODE_GOOD && UA_Variant_hasScalarType(&value, &UA_TYPES[UA_TYPES_STRING])) {
       ManufactureName2 =  *(UA_String *) value.data;
       UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Furnace Manufacturer Name is %.*s", (int)ManufactureName2.length, ManufactureName2.data);
    }
    //Read the furnace model Number
    retval = UA_Client_readValueAttribute(client, UA_NODEID_STRING(2, "C1_CF1_ModelNumber"), &value);

    if(retval == UA_STATUSCODE_GOOD && UA_Variant_hasScalarType(&value, &UA_TYPES[UA_TYPES_INT32])) {
	ModelNumber2 = *(UA_Int32 *) value.data;
        UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Funace Model Number is %d", ModelNumber2);
    }

    //read the state of furnace door

    retval = UA_Client_readValueAttribute(client, UA_NODEID_STRING(2, "C1_CF1_State"), &value);
    if(retval == UA_STATUSCODE_GOOD && UA_Variant_hasScalarType(&value, &UA_TYPES[UA_TYPES_BOOLEAN])) {
       state =  *(UA_Boolean *) value.data;
       //UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Furnace state is %i", state);
       //UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Furnace state is %s", state ? "true" : "false");
       UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Furnace state is %s", state == UA_TRUE ? "true" : "false");
    } else {
       UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Furnace state not received and %x returned value ", retval);
    }


    // set the state to true and read again
    //state = true;
    if(state == UA_FALSE)
        state = UA_TRUE;
    else
        state = UA_FALSE;

    UA_Variant *myVariant = UA_Variant_new();
    UA_Variant_setScalarCopy(myVariant, &state, &UA_TYPES[UA_TYPES_BOOLEAN]);
    retval = UA_Client_writeValueAttribute(client, UA_NODEID_STRING(2, "C1_CF1_State"), myVariant);
    if(retval != UA_STATUSCODE_GOOD ) {
       UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Furnace state could not be set and %x returned value ", retval);
    }
    UA_Variant_delete(myVariant);

    // read again
    retval = UA_Client_readValueAttribute(client, UA_NODEID_STRING(2, "C1_CF1_State"), &value);
    if(retval == UA_STATUSCODE_GOOD && UA_Variant_hasScalarType(&value, &UA_TYPES[UA_TYPES_BOOLEAN])) {
       state =  *(UA_Boolean *) value.data;
       UA_LOG_INFO(UA_Log_Stdout, UA_LOGCATEGORY_USERLAND, "The Furnace state is %s", state ? "true" : "false");
    } 

    /* Clean up */
    //UA_Variant_clear(&value);
    UA_Client_delete(client); /* Disconnects the client internally */
    return EXIT_SUCCESS;
}
