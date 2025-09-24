#include<iostream>
#include<cstdlib>
using namespace std;
int main(){
	int returnCode = system("python ./scripts/main.py");
	cout<<returnCode;
	return 0;
}
