#pragma once
#include "pch.h"


using namespace std;

namespace DssUtility
{


	string Format(float x, int precision);
	string FormatDecimalPlaces(float f, int places);
	bool Replace(std::string& str, const std::string& from, const std::string& to);
    string ReplaceAll(const std::string& str, const std::string& from, const std::string& to);
	bool StringsEqualIgnoreCase(string s1, string s2);
	string ToUpper(string line);
	string ToLower(string line);
	vector<string> Split(string line, string delimiter);
	int IndexOf(string line, string search);

	vector<string> FileReadAllLines(string fileName);

}
 