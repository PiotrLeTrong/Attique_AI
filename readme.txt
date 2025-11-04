Readme... Readme!

1. Run the 01_set_up.py file to get the code on finding and initially cleaning the pdf file into csv.
	a. Logic is to convert the PDF into a list file where each list is a string extraction of the PDF file. 
	b. Combine the list pages we need into 1 string. This is to keep the internal logic of the text file together and keep the questions associated to one another correctly.
	c. System sets up strict parameters for the process to hold unto. 
	d. the JSON data is crammed back into csv format. This is because the intermediate files tend to be used by non technically proficient users. 
2. 02_answering.py to answer questions.
	a. Converting the csv data into JSON ( this took forever because I am a silly goose)
	b. Turn each JSON entry into a query for the API to read and answer appending into the JSON process. 
	c. Export JSON into to the CSV - Not done

3. Other tasks
	The bottle-neck was figuring out how to feed the API the JSON data. But once I would've figured it out getting the logic of the translation and evaluator simple.
	For translation I would've evaluated the translatin from ENG to POL by translating POL into ENG to see if there are large deviations. 
	