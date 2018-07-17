/*
 * FemException.h
 *
 *  Created on: Nov 22, 2011
 *      Author: tcn45
 */

#ifndef FEMEXCEPTION_H_
#define FEMEXCEPTION_H_

#include <exception>
#include <iostream>
#include <sstream>
#include <string>

#define FEM_EXCEPTION_LOCATION __FUNCTION__,__FILE__,__LINE__

typedef int FemErrorCode;

class FemException : public std::exception
{

public:

  FemException(const std::string aExText) throw ();
  FemException(const FemErrorCode aExCode, const std::string aExText) throw ();
  FemException(const FemErrorCode aExCode, const std::string aExText, const std::string aExFunc,
      const std::string aExFile, const int aExLine) throw ();

  virtual ~FemException(void) throw ();

  virtual const char * what() const throw ();
  virtual const char * where() const throw ();
  virtual FemErrorCode which() const throw ();

private:

  const FemErrorCode mExCode;
  const std::string mExText;
  const std::string mExFunc;
  const std::string mExFile;
  const int mExLine;

};

#endif /* FEMEXCEPTION_H_ */
