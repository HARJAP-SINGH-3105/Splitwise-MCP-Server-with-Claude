from mcp.server.fastmcp import FastMCP
import os
# import requests
from dotenv import load_dotenv
load_dotenv() 
from splitwise import Splitwise
from splitwise.group import Group
from splitwise.user import User
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
from datetime import datetime, timedelta
# Create an MCP server
mcp = FastMCP("Splitwise-App")




### List of friends -> Thier name and my net balance with them
### Can also return Net Balance from my side
@mcp.tool()
def fetch_friends_data():
    
    """
    Fetches a list of all the user's friends from Splitwise with relevant details.

    This function queries the connected Splitwise account and returns a list of dictionaries,
    where each dictionary contains information about a friend, including:
    - `id`: Unique identifier of the friend.
    - `name`: Full name of the friend.
    - `balance`: The financial balance between the user and the friend.

    The balance indicates how much the user owes the friend (negative value),   
    how much the friend owes the user (positive value), or zero if settled.

    Returns:
        list[dict]: A list of dictionaries, each representing a friend with `id`, `name`, and `balance` keys.
    Example:
    {'Name': 'Sarvagya Jain', 'Id': 41096831, 'Balance': '220.5'}

    """

    try:
        api_key = os.getenv("API_KEY")
        cons_key = os.getenv("CONSUMER_KEY")
        cons_secret = os.getenv("CONSUMER_SECRET")
        sobj = Splitwise(cons_key,cons_secret,api_key =api_key)

        my_friends = sobj.getFriends()
        friend_list= []
        for friend in my_friends:
            
            my_dict = {}
            name = friend.getFirstName()
            if friend.getLastName():
                name += " " + friend.getLastName()
            
            friend_id = friend.getId()

            balance = 0
            if len(friend.getBalances()):
                balance =friend.getBalances()[0].getAmount()
            
            my_dict['Name'] = name
            my_dict['Id'] = friend_id
            my_dict['Balance'] = balance

            friend_list.append(my_dict)
        
        return friend_list
    
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


@mcp.tool()
def get_expenses_last_n_days(num_days: int):
    """
    Retrieves the user's expenses from the last `num_days` days.

    This function connects to the user's Splitwise account and fetches all expense records
    created in the past specified number of days. Each expense is returned as a dictionary 
    containing key details of the transaction.

    Args:
        num_days (int): The number of past days for which to retrieve expense records.

    Returns:
        list[dict]: A list of dictionaries where each dictionary represents an expense and contains:
            - 'Id of Expense': Unique identifier for the expense.
            - 'Description': A short description of the expense.
            - 'Cost(Expense)': The amount spent.
            - 'Details of transaction': Any additional notes or details, if available.
            - 'Created by ': The name of the user who created the expense.
            - 'Date of Expense': The ISO date-time string when the expense was recorded.
            - 'Group Name': The name of the group the expense belongs to (or 'Non-group expenses').
            - 'Currency code of transaction': Currency used for the transaction (e.g., 'USD').

    Example:
        get_expenses_last_n_days(7)
        [{
            'Id of Expense': 3878839201,
            'Description': 'Testing',
            'Cost(Expense)': '10.0',
            'Details of transaction': None,
            'Created by ': 'Harjap',
            'Date of Expense': '2025-06-22T16:16:17Z',
            'Group Name': 'Non-group expenses',
            'Currency code of transaction': 'USD'
        }]
    """

    try:
        start_date= (datetime.today() - timedelta(days=num_days)).strftime("%Y-%m-%d")
        end_date= (datetime.today() - timedelta(days=-1)).strftime("%Y-%m-%d")

        api_key = os.getenv("API_KEY")
        cons_key = os.getenv("CONSUMER_KEY")
        cons_secret = os.getenv("CONSUMER_SECRET")
        sobj = Splitwise(cons_key,cons_secret,api_key =api_key)
        expenses = sobj.getExpenses(dated_after=start_date, dated_before=end_date)


        all_exp = []
        for exp in expenses:
            dict_exp = {}
            dict_exp['Id of Expense'] = exp.getId()
            dict_exp['Description'] =  exp.getDescription()
            dict_exp['Cost(Expense)'] = exp.getCost()
            dict_exp['Details of transaction'] = exp.getDetails()
            dict_exp['Created by ']  =   exp.getCreatedBy().getFirstName()
            dict_exp['Date of Expense'] = exp.getDate()
            dict_exp['Group Name'] = sobj.getGroup(exp.getGroupId()).getName()
            dict_exp["Currency code of transaction"]= exp.getCurrencyCode()

            all_exp.append(dict_exp)
        
        return all_exp
    
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"
    

@mcp.tool()
def create_splitwise_expense(participants: list, paid_by: str, amount: float, description: str):
    """
    Creates a new expense in the user's Splitwise account.

    This function adds a new expense entry by taking the list of people involved in the transaction,
    the name of the person who paid, the total amount paid, and a brief description. 
    It then attempts to create the expense using the Splitwise API.

    Args:
        participants (list of str): First names of all people involved in the expense, including the payer.
        paid_by (str): First name of the person who paid the total amount.
        amount (float): Total amount paid for the expense.
        description (str): A short description of the expense (e.g., "Dinner", "Groceries").

    Returns:
        tuple:
            - expense_id (int or None): The unique ID of the created expense if successful, else None.
            - error (str or None): Error message if creation fails, otherwise None if successful.

    Example:
        >>> create_splitwise_expense(["Alice", "Bob"], "Alice", 40.0, "Dinner")
        (388849103, None)
    """

    try:
        api_key = os.getenv("API_KEY")
        cons_key = os.getenv("CONSUMER_KEY")
        cons_secret = os.getenv("CONSUMER_SECRET")
        sobj = Splitwise(cons_key,cons_secret,api_key =api_key)
        expense = Expense()
        expense.setCurrencyCode('INR')
        expense.setCost(str(amount))
        expense.setDescription(description)
        contri = amount/len(participants)
        users_list = []
    
    

        my_friends = sobj.getFriends()
        dict_info = {}
        me = sobj.getCurrentUser()
        my_name = me.getFirstName()
        my_id = me.getId()
        dict_info[my_name] = my_id

        for friend in my_friends:
            f_name = friend.getFirstName()
            f_id = friend.getId()
            dict_info[f_name] = f_id    ## Wonders what if two persons have same name :)

                

        for item in participants:
            try:
                name_id = dict_info[item]   ## What if name is not present in dictionary
            except:
                continue
            user = ExpenseUser()
            user.setId(name_id)
            if item==paid_by:
                user.setPaidShare(str(amount))
            else:
                user.setPaidShare('0')   

            user.setOwedShare(str(contri))
            users_list.append(user)
            
        expense.setUsers(users_list)
        

        expense, errors = sobj.createExpense(expense)

        if errors==None:
            return "Congrats, Expense added successfully!!"

        return "Failed, Not able to add expense."
    

    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


@mcp.tool()
def create_splitwise_group(group_name: str, first_names: list, last_names: list, emails: list):
    """
    Creates a new group on Splitwise and adds specified users to it.

    This function creates a group with the given name and adds each user to the group based on their
    first name, last name, and email address. All lists must be of equal length and in matching order.

    Args:
        group_name (str): The name of the group to be created (e.g., "Trip to Dubai").
        first_names (list of str): First names of all users to be added to the group.
        last_names (list of str): Last names of the users, corresponding to the first names.
        emails (list of str): Email addresses of the users, in the same order as names.

    

    Example:
        >>> create_splitwise_group(
                group_name="College Reunion",
                first_names=["Alice", "Bob"],
                last_names=["Smith", "Johnson"],
                emails=["alice@example.com", "bob@example.com"]
            )
        
    """

    try:
        api_key = os.getenv("API_KEY")
        cons_key = os.getenv("CONSUMER_KEY")
        cons_secret = os.getenv("CONSUMER_SECRET")
        sobj = Splitwise(cons_key,cons_secret,api_key =api_key)
        group = Group()
        group.setName(group_name)
        group, errors = sobj.createGroup(group)
        
        for i in range(len(first_names)):
            user = User()
            user.setFirstName(first_names[i])
            user.setLastName(last_names[i])
            user.setEmail(emails[i])
            success, user, errors = sobj.addUserToGroup(user, group.getId())

    
    except Exception as e:
        pass


if __name__ == "__main__":
    mcp.run()
