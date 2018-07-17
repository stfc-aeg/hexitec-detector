#include <iostream>
#include <map>
#include <vector>
#include <string>
#include <sstream>

#include "femApi.h"
#include "FemApiError.h"
#include "ExcaliburFemClient.h"

std::map<int, std::vector<int> > int_params;
std::map<int, std::vector<short> > short_params;
std::map<int, std::vector<double> > double_params;
std::map<int, std::vector<std::string> > string_params;

const unsigned int kClientTimeoutMsecs = 10000;

typedef struct {
	ExcaliburFemClient* client;
	FemApiError         error;
} FemHandle;

const char* femErrorMsg(void* handle)
{
	FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

    return (femHandle->error).get_string();
}

int femErrorCode(void* handle)
{
	FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

    return (femHandle->error).get_code();
}

int femInitialise(void* ctlHandle, const CtlCallbacks* callbacks, const CtlConfig* config, void** handle)
{

	int rc = FEM_RTN_OK;

	// Initialise FEM handle and client objects, which opens and manages the connection with the FEM
	FemHandle* femHandle = new FemHandle;
	femHandle->client = NULL;
	*handle = reinterpret_cast<void*>(femHandle);

	try
	{
		femHandle->client = new ExcaliburFemClient(ctlHandle, callbacks, config, kClientTimeoutMsecs);

	}
	catch (FemClientException& e)
	{
		femHandle->error.set() << "Failed to initialise FEM connection: " << e.what();
		rc = FEM_RTN_INITFAILED;
	}


    return rc;
}

void femSetLogFunction(logFunc log_func)
{
    // Do nothing in stub API as no output needs to be logged
}

int femGetId(void* handle)
{
	FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

    return (femHandle->client)->get_id();
}

void femClose(void* handle)
{

	FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

	if (femHandle->client != NULL) {
		delete femHandle->client;
	}

	delete femHandle;
}

int femSetInt(void* handle, int chipId, int id, size_t size, size_t offset, int* value)
{
    int rc = FEM_RTN_OK;

    int_params[id] = std::vector<int>(value, value + size);

    return rc;
}

int femSetShort(void* handle, int chipId, int id, std::size_t size, size_t offset, short* value)
{
	int rc = FEM_RTN_OK;

	short_params[id] = std::vector<short>(value, value+size);

	return rc;
}


int femSetFloat(void* handle, int chipId, int id, std::size_t size, size_t offset, double* value)
{
	int rc = FEM_RTN_OK;

	double_params[id] = std::vector<double>(value, value+size);

	return rc;
}


int femSetString(void* handle, int chipId, int id, size_t size, size_t offset, char** values)
{
	int rc = FEM_RTN_OK;

	string_params[id] = std::vector<std::string>(values, values+size);

	return rc;
}

int femGetInt(void* femHandle, int chipId, int id, std::size_t size, int* value)
{
    int rc = FEM_RTN_OK;

    if (int_params.count(id) > 0) {
        for (size_t i = 0; i < size; i++) {
            value[i] = int_params[id][i];
        }
    } else {
        for (size_t i = 0; i < size; i++) {
            value[i] = id + i;
        }
    }

    return rc;
}

int femGetShort(void* femHandle, int chipId, int id, std::size_t size, short* value)
{
    int rc = FEM_RTN_OK;

    if (short_params.count(id) > 0) {
        for (std::size_t i = 0; i < size; i++) {
            value[i] = short_params[id][i];
        }
    } else {
        for (std::size_t i = 0; i < size; i++) {
            value[i] = id + i;
        }
    }

    return rc;
}

int femGetFloat(void* femHandle, int chipId, int id, std::size_t size, double* value)
{
    int rc = FEM_RTN_OK;

    if (double_params.count(id) > 0) {
        for (std::size_t i = 0; i < size; i++) {
            value[i] = double_params[id][i];
        }
    } else {
        for (std::size_t i = 0; i < size; i++) {
            value[i] = double(id + i);
        }
    }

    return rc;
}


int femGetString(void* handle, int chipId, int id, size_t size, char** value)
{
	int rc = FEM_RTN_OK;

	if (string_params.count(id) > 0) {
		for (std::size_t i = 0; i < size; i++) {
			value[i] = const_cast<char*>(string_params[id][i].c_str());
		}
	} else {
		for (std::size_t i = 0; i < size; i++) {
			std::stringstream out;
			out << "string " << i;
			value[i] = const_cast<char*>(out.str().c_str());
		}
	}
	return rc;
}


int femCmd(void* handle, int chipId, int id)
{
    int rc = FEM_RTN_OK;

    FemHandle* femHandle = reinterpret_cast<FemHandle*>(handle);

    switch (id)
    {
        case FEM_OP_STARTACQUISITION:
        case FEM_OP_STOPACQUISITION:
        case FEM_OP_LOADPIXELCONFIG:
        case FEM_OP_FREEALLFRAMES:
        case FEM_OP_LOADDACCONFIG:
        case FEM_OP_FEINIT:
        case FEM_OP_REBOOT:
            // Do nothing for now
            break;

        default:
            rc = FEM_RTN_UNKNOWNOPID;
            (femHandle->error).set() << "femCmd: illegal command ID: " << id;
    }

    return rc;
}

