#include "FemApiError.h"

FemApiError::FemApiError() {

}

FemApiError::~FemApiError() {
    //error_string_ = os.str();
}

std::ostringstream& FemApiError::set() {
	os.str("");
	os.clear();
    return os;
}

std::ostringstream& FemApiError::set(const int error_code) {
    error_code_ = error_code;
    return os;
}

const char* FemApiError::get_string(void) {
	error_string_ = os.str();
    return error_string_.c_str();
}

const int FemApiError::get_code(void) {
    return error_code_;
}

//std::string FemApiError::error_string_ = "";
//int FemApiError::error_code_ = 0;
