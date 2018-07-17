#include <iostream>
#include <string>
#include <sstream>

class FemApiError
{
public:
  FemApiError();
  virtual ~FemApiError();
  std::ostringstream& set();
  std::ostringstream& set(const int error_code);
  const char* get_string(void);
  const int get_code(void);

protected:
  std::ostringstream os;

private:
  FemApiError(const FemApiError&);
  FemApiError& operator =(const FemApiError&);
  std::string error_string_;
  int error_code_;

};
