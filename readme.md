"BUT YEAH MOSTLY QUERIES WOULD BE FROM OPEN ORDERS NOT ALL BUT YEAH MOSTLY FROM OPEN ORDERS AS SAID BY CLIENT"

we have to put feedback option also if user says BAD or GOOD
###################################################################################################
i hve to make response more conersational
deploy
optimize or make a trained model for faster inferece like h5
update state provisional data

if there are moree than one permit info remove all , also if mentioned state is none state value is none aand global state value is none and there is pemrit info then remove it dont fetch it

*************************************** prompt for state ***************************************
keys in response is like this ['state_name: california', 'state_fee'] by first groq llm api hit by func ask_llm
whatever response comes from ask_llm if it has state_name with value then take value from there and store in State_value. If state_name is there but there is no value then fill State_value with None

i want state filtering by this->
if mentioned_state is not there in user input and it is none then check State_value if it is there if yes then pass that value to mentioned state if not then check check global_state_name if it is present then pass this in mentioned_value but pass global_state_value in mentioned_state only iff permit_info key is present in response by ask_llm if not then pass none in mentioned_state(which means there would be no filtering by state if it is none)
***************************************

now i want that if mentioned_state has some value already then go with it and if not then check 'State_value' if it has value then it should be passed to mentioned_state variable


if state_name is mentioned in keys then filter with that state only
save that state_name is variable if permit info comes and no state is choosen then use this state.

for permit info pass only last query and if more than one permit info are there then filter acc to global state
currently i am just passing 5 queries to both apis calls if needed the i will pas response also to the seocond groq api

when permit info comes in keys then history should be clean and start again

permit me max 3 queries , state name save karana h

challenges:
a. follow up required to be worked on
**Get project git ready and api and how to deploy on server
*i have to refine the responses for the state provision file from the RAG ,last time i used nemotron

exmaples and samples work a lot for AI to understand how user wants the response

###################################################################################################

Pass metadata abt user and his order if he is on some order so that llm can know about the user and also he's querying on his way with order or not with his order, also by metadata llm can tell if he is a driver or client in this order or his past orders.

Currently i am directly connecting voice to main code but for commercial purpose better to first make api and then connect NOT SURE




###################################################################################################

Bugs:
2. how many orders am i having in past month
intent is coming YES for last time / recently
3. i think i have to connect states info with permit so that llm can answer from both states info and permit as well
some permits do not have axle spacing and overall weight
4. i think main brain passes more than one permit for final response if there are two same state in same order which would be hectic for last api to process it
5. i can also remove month name from intent prompt as it can be found by my code only but yeah user can also say JAN FEB mayb
6. Filtering date is starting from the 2 or 3  ot 5 or 7 of the month i think it is minusing 30 days 
-> for past 7 months: "Filtering orders between: 2024-07-05 and 2025-02-01"


###################################################################################################

Optimize:
1. i am running these 5 functions for all queries when i am having switches then i knw that which specific function to run by date by last time or by month or by status etc.
2. REMOVE USELESS VALUES FROM PRPT.TXT AS IT IS TAKING MORE TOKEN AND ALSO MAKE SURE THAT IT 
3. remove overall dimensions from this schema as diensions are already present in perit
4. remove START_DATE FROM SYS_MSG if responses are still same

###################################################################################################

Improvements:
1. if state asked in query is not in current order or route then it should see the provisonal file
2. i didnt used indexing in my old code i think i should integrate this code with my main new brain code
3. a variable which will hold order id for every query|| then after this there will come buffer memory
4. i think i have to create summary, meta data of the data/order which is being passed like in how many orders i wwas driver, client and i should give details about me to the llm my name , phone number, id , orders in which i was client, driver
5. i can generate intent by one api only i just have to change my prompt and now i can use one more api to filter data more or just for final response one api
6. if user talk between multiple orders then i have to create order ids section || Maybe
7. query: what is the state fee for texas in my last order
for this it is fetching all orders with all states , if i use indexing then only last order and then texas should be fetched
8. currently i am not using indexing in code as i have to do some changes for that, i am fetching all the data and then performing analysis on that
9. ![alt text](old\image.png)
in above image driver is already at texas and asking when was the the last time he went to texas then he should check the last time texas except current order, but other case can be
10. if he's not delivering any order or just want to know when was the last time texas he visited so i have to count this last order also
11. Custom Pipeline: You can create your own custom pipeline using libraries like asyncio (for asynchronous operations) to manage concurrent requests to Groq and your DB. This can help optimize the overall response time.
12. add more functions commodity , transactions, route ideas in schema and functions to fetch them
13. Caching and memory (sessional or long term)
###################################################################################################

Possibilities:
1. Directly connect code with voice assistant or make api and then connect it to voice assistant

#####################################################################################################

Cases:

2. Question can be "how many states i visited in my past two orders" so now how to understand intent and which query to fetch , just fetch last two orders in the list as it is sorted
3. it can also ask like from past 3 weeks or 2 months
4. when user ask this:
Are there any exceptions to the legal dimensions in Oregon?
permit info is returned for all states as oregon was not in his order so now we want to access state provisional file
5. query can be like my last closed order or my last open order or second last open or close order

#####################################################################################################

Tips:
1. if any response is not as expected please change in starting or find that code snippet or funtion where to change
Some other approach
2. KAHI FASE TOH EK OR API HIT KRWALIO , MAJBURI ME BTW NOT RECOMMENED



