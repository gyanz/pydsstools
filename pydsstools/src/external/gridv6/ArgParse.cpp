#include "pch.h"
#include "ArgParse.h"


ArgParse::ArgParse(int argc, char**argv)
{
	for (int i = 1; i < argc; i++)
	{
		args.push_back((string)argv[i]);
	}
}


ArgParse::~ArgParse()
{
}
string ArgParse::GetArg(string input, bool required)
{
	return GetArg(input, required, "");
}
string ArgParse::GetArg(string input, bool required, string defaultValue)
{
	string tempString = input + "=";
	for (int i = 0; i < args.size(); i++)
	{
		for (int j = 0; j < tempString.length(); j++)
		{
			if (tolower(args[i][j]) == tolower(tempString[j]))
			{
				string command = args[i].substr(0, args[i].find("="));
				if (args[i][j] == command[command.length() - 1])
				{
					return args[i].substr(command.length() + 1, args[i].length());
				}
				else 
				{
					continue;
				}
			}
			else 
			{
				break;
			}
		}
	}
	return defaultValue;
}
