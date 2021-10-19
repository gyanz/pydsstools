#pragma once
#include "pch.h"
#include "DssUtility.h"
extern "C"
{
#include "heclib.h"
}

using std::string;

class EsriAsciiGrid
{
public:
	EsriAsciiGrid();
	~EsriAsciiGrid();
	static int WriteArcTextFile(zStructSpatialGrid * grid, string outFileName, int precision);
	static int ReadGridfromArc(string inFile, zStructSpatialGrid *grid);

};

