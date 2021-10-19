
#include "DssUtility.h"

//using namespace std;
using std::string;

namespace DssUtility
{


	/*
	Format precision of number
	*/
	string Format(float x, int precision)
	{
		stringstream stream;
		stream << fixed << setprecision(precision) << x;
		string s = stream.str();
		return s;
	}
	/*
	Format float with specifed number of places after decimal
	*/
	string FormatDecimalPlaces(float f, int places)
	{
		string rval = "";
		//  Return _value as RWCString (e.g., "1.23")
		//  If no precision set (-1), use default print
		//  If not set, return a blank string
		char string1[10], string2[20];

		if (fabs(f) < 1.e10) {
			if (places >= 0) {
				//  Make a "format" string
				sprintf(string1, "%%.%df", places);
				//  Write the number using that format string
				sprintf(string2, string1, f);
			}
			else {
				sprintf(string2, "%f", f);
			}
		}
		else {
			sprintf(string2, "%e", f);
		}

		return rval = string2;
	}



	//https://stackoverflow.com/questions/3418231/replace-part-of-a-string-with-another-string

	bool Replace(std::string& str, const std::string& from, const std::string& to) {
		size_t start_pos = str.find(from);
		if (start_pos == std::string::npos)
			return false;
		str.replace(start_pos, from.length(), to);
		return true;
	}

	string ReplaceAll(const std::string& str, const std::string& from, const std::string& to) {
		string rval = str;
		if (from.empty())
			return rval;
		size_t start_pos = 0;
		while ((start_pos = rval.find(from, start_pos)) != std::string::npos) {
			rval.replace(start_pos, from.length(), to);
			start_pos += to.length(); // In case 'to' contains 'from', like replacing 'x' with 'yx'
		}
		return rval;
	}
	bool StringsEqualIgnoreCase(string s1, string s2)
	{
		size_t len = s1.length();

		if (s2.length() != len)
			return 0;
		for (string::size_type i = 0; i < len; ++i)
			if (tolower(s1[i]) != tolower(s2[i]))
				return 0;

		return 1;
	}

	string ToUpper(string line)
	{
		string s;
		for (auto x : line)
		{
			x = toupper(x);
			s += x;
		}
		return s;
	}

	string ToLower(string line)
	{
		string s;
		for (auto x : line)
		{
			x = tolower(x);
			s += x;
		}
		return s;

	}


	vector<string> Split(string line, string delimiter)
	{
		vector<string> splitData;
		for (auto i = line.cbegin(); ; )
		{
			auto r = search(i, line.cend(), delimiter.cbegin(), delimiter.cend());
			splitData.push_back(string(i, r));
			if (r == line.cend()) break;
			i = r + delimiter.length();
		}
		return splitData;
	}

	int IndexOf(string line, string search)
	{
		auto x = line.find(search);
		if (x == string::npos)
		{
			return -1;
		}
		return(int)x;
	}

	vector<string> FileReadAllLines(string fileName)
	{
		vector<string> rval;
		std::string line;
		std::ifstream file(fileName);

		while (std::getline(file, line)) {
			rval.push_back(line);
		}

	return rval;

	}


}
