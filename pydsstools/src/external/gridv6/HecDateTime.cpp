#include "HecDateTime.h"



HecDateTime::HecDateTime(string date, string time) {

//dateToYearMonthDay()
}

HecDateTime::~HecDateTime() {	}

bool HecDateTime::Undefined(int julian)
{
	return julian == UNDEFINED_TIME;
}

bool HecDateTime::IsDefined() {
	return true; // TO DO.
}

string HecDateTime::ToString()
{
	return "";
}

int HecDateTime::Year() { return -1; }
int HecDateTime::Month() { return -1; }


/*
HecDateTime startTime, endTime;
	// Extract path parts from path
	int startIndex, endIndex;

	// Extract start and end times from D and E parts, if possible
	char colon[2] = { ':', '\0' };
	if (Dpart != "") {
		endIndex = DssUtility::IndexOf(Dpart, ":");
		if (endIndex != -1) {
			startDateString = Dpart.substr(0, endIndex);
			startIndex = ++endIndex;
			endIndex = Dpart.length();
			startTimeString = Dpart.substr(startIndex, (endIndex - startIndex));
			DssUtility::ToUpper(startDateString);
			cout << "\nStart Date: " << startDateString
				<< "\nStart Time: " << startTimeString << endl;
		}
	}

	if (Epart != "") {
		endIndex = DssUtility::IndexOf(Epart, ":");
		if (endIndex != -1) {
			endDateString = Epart.substr(0, endIndex);
			startIndex = ++endIndex;
			endIndex = Epart.length();
			endTimeString = Epart.substr(startIndex, (endIndex - startIndex));
			DssUtility::ToUpper(endDateString);
			cout << "\nEnd Date: " << endDateString
				<< "\nEnd Time: " << endTimeString << endl;
		}
	}

	if (startDateString != "" && startTimeString != "") {
		startTime.Set(startDateString, startTimeString);
	}
	if (endDateString != "" && endTimeString != "") {
		endTime.Set(endDateString, endTimeString);
	}

	*/
