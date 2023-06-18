## Task description
Here you can describe what tasks you decided to solve.
> Please provide a short description of your project.

This is a backend service consiting of two simple enpoints, built using flask rest (https://flask-restx.readthedocs.io/en/latest/index.html) alongside a few other flask dependencies. It takes a form post request on the endpoint /api/uploadfile/, with two fields, a field named 'file' containing a users consupmtion data in the form of a .json file (`consumption.json`), and a string field name, containing a users name/id etc... (this is simply so that we can query it later, here the session_id would be more optimal). Our second endpoint is a get request found under `/api/calculate/<username>`, and this is where the magic happends. This endpoint calls on one of our functions under the `HelperMethods` class, and is where we calculate how much each provider would have cost the user based on his/her historical data. It is a rather crude implementation, but it is what i ended up with with the time and resoruces at hand. 

The endpoints returns this:
```json
{
	"best_option": {
		"name": "Vest Energi",
		"pricingModel": "fixed",
		"fixedPrice": 1.5,
		"cost_based_on_user_history": {
			"NO1": 2522.4090000000015,
			"NO2": 2522.4090000000015,
			"NO3": 2522.4090000000015,
			"NO4": 2522.4090000000015,
			"NO5": 2522.4090000000015
		}
	},
	"other_options": [
		{
			"name": "Øst Energi",
			"pricingModel": "variable",
			"variablePrice": 1.5,
			"cost_based_on_user_history": {
				"NO1": 2522.4090000000015,
				"NO2": 2522.4090000000015,
				"NO3": 2522.4090000000015,
				"NO4": 2522.4090000000015,
				"NO5": 2522.4090000000015
			}
		},
		{
			"name": "Nord Energi",
			"pricingModel": "spot-hourly",
			"fixedPrice": 0.3,
			"cost_based_on_user_history": {
				"NO1": 3411.334210960002,
				"NO2": 3411.334210960002,
				"NO3": 2065.048722099999,
				"NO4": 1439.8462258299996,
				"NO5": 3452.162365200002
			}
		},
		{
			"name": "Nord Energi",
			"pricingModel": "spot-monthly",
			"fixedPrice": 0.3,
			"cost_based_on_user_history": {
				"NO1": 5130.948236758778,
				"NO2": 5130.895220543988,
				"NO3": 3514.2737383059266,
				"NO4": 1861.9506413982183,
				"NO5": 5158.333027218974
			}
		}
	]
}
```
Showing the user the best option based on price, and the other alternatives.

## How to run
> Remember to package all dependencies!

The program comes with an accompanying mysql databasase, i have provided a docker compose file which will start it up with the correct enviournemnt variables. Here one is ofcource free to utilize any other mysql database, but remember to update the .env file accordingly. For the python runtime, i have provided a `requirements.txt` file with the neccesarry packages, pandas is also included, but this can be removed if wished and is not neccesarry to run the application. 

I used python 3.11, but considering im not using any nieche packages, anything above 3.10 should be ok. 
Quickguide to run on macos/linux:

Ensure Docker is installed.

From project root:

`docker compose up --build` (optional -d flag)

Create venv:

`python -m venv .venv`

Move into the `api` folder:
`cd api`

Install dependencies:
`pip install -r api/requirements.txt`

run application:
`flask db migrate -m "Initial Migration" && flask run`

Application shold now be live on localhost:5000. 

## Comments
There are tons of comments to be had about this applications, it did not go quite the direction i intended, but considering a hectic weekend i think it is ok. I stand my most of my decisions and will gladly explain why i went for the structure that i did, (going with mongodb is most likely smarter considering the type of data we are dealing with etc..) My plan was to dockerize the flask application, as might be eminent with the Dockerfile amd .dockerignore, however i had some last minute resistance from the mysql-flask local docker network, and went back to simply running it thorugh a .venv for package management.

Thank you for an intresting task. 
