/*
 * FemException.cpp
 *
 *  Created on: Nov 22, 2011
 *      Author: tcn45
 */

#include "FemException.h"

FemException::FemException(const std::string aExText) throw () :
    mExCode(-1),
    mExText(aExText),
    mExFunc("unknown"),
    mExFile("unknown"),
    mExLine(-1)
{
}

FemException::FemException(const FemErrorCode aExCode, const std::string aExText) throw () :
    mExCode(aExCode),
    mExText(aExText),
    mExFunc("unknown"),
    mExFile("unknown"),
    mExLine(-1)
{
}

FemException::FemException(const FemErrorCode aExCode, const std::string aExText,
    const std::string aExFunc, const std::string aExFile, const int aExLine) throw () :
    mExCode(aExCode),
    mExText(aExText),
    mExFunc(aExFunc),
    mExFile(aExFile),
    mExLine(aExLine)
{
}

FemException::~FemException() throw ()
{
}

const char * FemException::what() const throw ()
{
  return mExText.c_str();
}

const char * FemException::where() const throw ()
{
  std::ostringstream ostr;
  ostr << "function: " << mExFunc << " file: " << mExFile << " line: " << mExLine;
  return (ostr.str()).c_str();
}

FemErrorCode FemException::which() const throw ()
{
  return mExCode;
}
