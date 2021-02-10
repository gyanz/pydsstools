#pragma once
#include <string>

extern "C"
{
#include "heclib.h"
}

using std::string;

class HecDateTime
{
public:
	HecDateTime(string date, string time);
	~HecDateTime();
	static bool Undefined(int julian);
	bool IsDefined();
	string ToString();
	int Year();
	int Month();
	void Set(std::string date, std::string stime) {} // to do...}
};
