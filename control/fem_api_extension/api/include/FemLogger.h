/*
 * FemLogger.h - logging capability for FEM client classes.
 *
 * This header implements a FemLogger class for FEM clients, allowing
 * log messages to be redirected to a function call, e.g. in an enclosing
 * application or messaging layer. This class is derived from the
 * Dr Dobbs Journal example found at
 *
 * http://www.drdobbs.com/cpp/logging-in-c/201804215
 *
 * Tim Nicholls, STFC Application Engineering Group.
 */
#ifndef __FEMLOGGER_H__
#define __FEMLOGGER_H__

#include <iostream>
#include <sstream>
#include <string>
#include <stdio.h>
#include <sys/time.h>

// Foward declaration of timestamp formatting function
inline std::string NowTime();

// Enumerated log levels
enum TLogLevel {logERROR, logWARNING, logINFO, logDEBUG};

// Typedef for pointer to external logging function.
typedef void (*TLogFunc)(const unsigned int, const char*);

// Default FEM ID
#define DEFAULT_FEM_ID -1

// FemLogger class definition
class FemLogger
{
public:

    FemLogger();
    virtual ~FemLogger();
    std::ostringstream& Get(TLogLevel level = logINFO);
    std::ostringstream& Get(int fem_id, TLogLevel level = logINFO);

    static TLogLevel& ReportingLevel();
    static std::string ToString(TLogLevel level);
    static TLogLevel FromString(const std::string& level);
    static void SetLoggingFunction(TLogFunc log_func);

protected:

    std::ostringstream os;      // Stringstream used to build logging message

private:

    FemLogger(const FemLogger&);
    FemLogger& operator =(const FemLogger&);

    static TLogFunc log_func_; // External logging function pointer
    TLogLevel level_;          // Logging level for current message
    int fem_id_;               // ID of FEM logging message

};

// Constructor for FemLogger - sets up default member values
inline FemLogger::FemLogger() :
    level_(logINFO),
    fem_id_(DEFAULT_FEM_ID)
{
}

// Get a logger stream with a given logging level set
inline std::ostringstream& FemLogger::Get(TLogLevel level)
{
    level_ = level;
    return os;
}

// Get a logger stream with a given FEM id and logging level set
inline std::ostringstream& FemLogger::Get(int fem_id, TLogLevel level)
{
    fem_id_ = fem_id;
    return this->Get(level);
}

// FemLogger destructor - formats and emits log message
inline FemLogger::~FemLogger()
{
    std::ostringstream msg;

    // If FEM ID is set, prefix messsage with it
    if (fem_id_ != DEFAULT_FEM_ID)
    {
        msg << "FEM " << fem_id_ << ": ";
    }

    // Append message stream to prefix
    msg << os.str();

    // If the logging function is configured, call that, otherwise emit a simple formatted
    // message on stdout using iostream.
    if (log_func_ != NULL) {
        log_func_(level_, msg.str().c_str());
    }
    else {
        std::cout << NowTime() << " - " << ToString(level_) << " : " << msg.str() << std::endl;
    }
}

// Sets and returns the current log reporting level, defaulting to debug. This allows the
// reporting level to be set simply in code, e.g. FemLogger::ReportingLevel = logINFO
inline TLogLevel& FemLogger::ReportingLevel()
{
    static TLogLevel reportingLevel = logDEBUG;
    return reportingLevel;
}

// Map a logging level onto a string name
inline std::string FemLogger::ToString(TLogLevel level)
{
    static const char* const buffer[] = {"ERROR", "WARNING", "INFO", "DEBUG"};
    return buffer[level];
}

// Map a logging level name on to the equivalent level
inline TLogLevel FemLogger::FromString(const std::string& level)
{
    if (level == "DEBUG")
        return logDEBUG;
    if (level == "INFO")
        return logINFO;
    if (level == "WARNING")
        return logWARNING;
    if (level == "ERROR")
        return logERROR;
    FemLogger().Get(logWARNING) << "Unknown logging level '" << level << "'. Using INFO level as default.";
    return logINFO;
}

// Set the external logging function to be used
inline void FemLogger::SetLoggingFunction(void (*log_func)(unsigned int level, const char* msg))
{
    log_func_ = log_func;
}

// Macros that allow simple logging to be performed in code
#define LOG(level) \
    if (level > FemLogger::ReportingLevel()) ; \
    else FemLogger().Get(level)

#define FEMLOG(fem, level) \
    if (level > FemLogger::ReportingLevel()) ; \
    else FemLogger().Get(fem, level)

// Function to format a simple timestamp for default logging
inline std::string NowTime()
{
    char buffer[11];
    time_t t;
    time(&t);
    tm r = {0};
    strftime(buffer, sizeof(buffer), "%X", localtime_r(&t, &r));
    struct timeval tv;
    gettimeofday(&tv, 0);
    char result[100] = {0};
    sprintf(result, "%s.%03ld", buffer, (long)tv.tv_usec / 1000);
    return result;
}

#endif //__FEMLOGGER_H__
