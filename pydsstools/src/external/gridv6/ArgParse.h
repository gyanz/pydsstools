#include <vector>
#include <string>
using std::string;
using std::vector;
#pragma once
class ArgParse
{
public:
	ArgParse(int argc, char**argv);
	~ArgParse();

	string GetArg(string input, bool required); 
	string GetArg(string input, bool required, string defaultValue);
	vector<string> args;

};

