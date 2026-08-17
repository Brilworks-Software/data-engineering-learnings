# Python Basics for Data Engineering

## 1. Introduction

Python is one of the most widely used programming languages in Data Engineering.

Python is commonly used for:

* Data extraction
* Data transformation
* Data cleaning
* ETL/ELT pipelines
* API integration
* File processing
* Automation
* Data validation
* Pandas
* PySpark
* Databricks
* Airflow and orchestration

This guide covers the Python fundamentals required before learning:

```text
Python
  ↓
Pandas
  ↓
SQL
  ↓
PySpark
  ↓
ETL
  ↓
Databricks
```

---

# 2. Running Python

Check Python version:

```bash
python3 --version
```

Activate the project virtual environment:

```bash
source .venv/bin/activate
```

Check which Python is being used:

```bash
which python
```

Expected:

```text
.../data-engineering-learnings/.venv/bin/python
```

Run a Python file:

```bash
python python/basics/example.py
```

---

# 3. Comments

Comments are ignored by Python and are used to explain code.

## Single-line comment

```python
# This is a comment

name = "Prince"
```

## Multi-line documentation

```python
"""
This is a multi-line string.
It can be used as documentation.
"""
```

For functions and classes, use docstrings:

```python
def calculate_total(price, quantity):
    """
    Calculate the total price.
    """
    return price * quantity
```

---

# 4. Variables

A variable stores a value.

```python
name = "Prince"
age = 25
salary = 50000.50
is_data_engineer = True
```

Python automatically determines the data type.

```python
print(name)
print(age)
print(salary)
print(is_data_engineer)
```

Check the type:

```python
print(type(name))
print(type(age))
print(type(salary))
print(type(is_data_engineer))
```

Output:

```text
<class 'str'>
<class 'int'>
<class 'float'>
<class 'bool'>
```

## Variable naming

Good:

```python
customer_name = "Prince"
customer_id = 101
total_orders = 10
```

Avoid unclear names:

```python
x = "Prince"
a = 10
```

Prefer descriptive names.

---

# 5. Python Data Types

| Type    | Example     | Description                  |
| ------- | ----------- | ---------------------------- |
| `str`   | `"India"`   | Text                         |
| `int`   | `100`       | Integer                      |
| `float` | `99.50`     | Decimal number               |
| `bool`  | `True`      | Boolean                      |
| `list`  | `[1, 2, 3]` | Ordered mutable collection   |
| `tuple` | `(1, 2, 3)` | Ordered immutable collection |
| `dict`  | `{"id": 1}` | Key-value collection         |
| `set`   | `{1, 2, 3}` | Unique values                |
| `None`  | `None`      | No value                     |

---

# 6. Strings

A string represents text.

```python
name = "Prince"
country = "India"

print(name)
print(country)
```

## Concatenation

```python
first_name = "Prince"
last_name = "Patel"

full_name = first_name + " " + last_name

print(full_name)
```

Output:

```text
Prince Patel
```

## f-strings

Prefer f-strings for formatting:

```python
name = "Prince"
age = 25

message = f"My name is {name} and I am {age} years old."

print(message)
```

## Common string methods

```python
name = "  PRINCE PATEL  "

print(name.strip())
print(name.lower())
print(name.upper())
print(name.replace("PRINCE", "John"))
```

Useful methods:

```text
strip()
lower()
upper()
replace()
split()
startswith()
endswith()
```

Example:

```python
email = "prince@example.com"

print(email.endswith(".com"))
```

---

# 7. Numbers

## Integer

```python
age = 25
orders = 100
```

## Float

```python
price = 99.99
tax = 18.50
```

## Arithmetic operators

```python
a = 10
b = 3

print(a + b)
print(a - b)
print(a * b)
print(a / b)
print(a // b)
print(a % b)
print(a ** b)
```

| Operator | Meaning        |
| -------- | -------------- |
| `+`      | Addition       |
| `-`      | Subtraction    |
| `*`      | Multiplication |
| `/`      | Division       |
| `//`     | Floor division |
| `%`      | Modulus        |
| `**`     | Power          |

---

# 8. Boolean Values

Boolean values are:

```python
True
False
```

Example:

```python
is_active = True

print(is_active)
```

Comparison operators:

```python
a = 10
b = 20

print(a == b)
print(a != b)
print(a > b)
print(a < b)
print(a >= b)
print(a <= b)
```

---

# 9. Lists

A list stores multiple values.

```python
locations = [
    "India",
    "USA",
    "UK",
    "Canada"
]
```

Access values:

```python
print(locations[0])
print(locations[1])
```

Python indexing starts from `0`.

```text
0 → India
1 → USA
2 → UK
3 → Canada
```

## Add

```python
locations.append("Australia")
```

## Remove

```python
locations.remove("UK")
```

## Length

```python
print(len(locations))
```

## Check existence

```python
if "India" in locations:
    print("India exists")
```

## Slicing

```python
numbers = [10, 20, 30, 40, 50]

print(numbers[0:3])
```

Output:

```text
[10, 20, 30]
```

---

# 10. Tuples

A tuple is similar to a list but cannot be modified after creation.

```python
coordinates = (23.02, 72.57)

print(coordinates[0])
print(coordinates[1])
```

Tuples are useful when values should remain unchanged.

---

# 11. Dictionaries

Dictionaries store key-value pairs.

They are extremely important in Data Engineering because APIs and JSON commonly use this structure.

```python
customer = {
    "id": 101,
    "name": "Prince",
    "country": "India",
    "age": 25
}
```

Access values:

```python
print(customer["name"])
print(customer["country"])
```

Add:

```python
customer["email"] = "prince@example.com"
```

Update:

```python
customer["age"] = 26
```

Remove:

```python
del customer["age"]
```

Safe access:

```python
print(customer.get("age"))
```

---

# 12. Nested Dictionaries

Real-world API and JSON data is often nested.

```python
customer = {
    "id": 101,
    "name": "Prince",
    "address": {
        "city": "Rajkot",
        "state": "Gujarat",
        "country": "India"
    }
}
```

Access nested data:

```python
print(customer["address"]["city"])
print(customer["address"]["country"])
```

---

# 13. List of Dictionaries

This structure is very important for Data Engineering.

```python
customers = [
    {
        "id": 101,
        "name": "Prince",
        "country": "India"
    },
    {
        "id": 102,
        "name": "John",
        "country": "USA"
    },
    {
        "id": 103,
        "name": "David",
        "country": "UK"
    }
]
```

Access the first customer:

```python
print(customers[0])
```

Access the first customer's name:

```python
print(customers[0]["name"])
```

---

# 14. Sets

A set stores unique values.

```python
countries = {
    "India",
    "USA",
    "India",
    "UK"
}

print(countries)
```

Duplicates are automatically removed.

Example:

```python
locations = ["India", "USA", "India", "UK"]

unique_locations = set(locations)

print(unique_locations)
```

Sets are useful for:

* Removing duplicates
* Membership checks
* Comparing collections

---

# 15. None

`None` represents the absence of a value.

```python
email = None

print(email)
```

Check for `None`:

```python
if email is None:
    print("Email is not available")
```

Prefer:

```python
is None
```

instead of:

```python
== None
```

---

# 16. Type Conversion

Convert between data types.

```python
age = "25"

age = int(age)

print(age)
print(type(age))
```

Other conversions:

```python
number = 100

print(str(number))
print(float(number))
```

Convert tuple to list:

```python
values = ("India", "USA", "UK")

locations = list(values)

print(locations)
```

---

# 17. Conditional Statements

Use `if`, `elif`, and `else`.

```python
age = 25

if age >= 18:
    print("Adult")
else:
    print("Minor")
```

Multiple conditions:

```python
score = 85

if score >= 90:
    grade = "A"
elif score >= 75:
    grade = "B"
elif score >= 60:
    grade = "C"
else:
    grade = "D"

print(grade)
```

---

# 18. Logical Operators

## AND

Both conditions must be true.

```python
age = 25
country = "India"

if age >= 18 and country == "India":
    print("Eligible")
```

## OR

At least one condition must be true.

```python
status = "SUCCESS"

if status == "SUCCESS" or status == "COMPLETED":
    print("Process completed")
```

## NOT

Reverses a condition.

```python
is_failed = False

if not is_failed:
    print("Process is successful")
```

---

# 19. For Loops

Loops allow us to process multiple records.

```python
locations = [
    "India",
    "USA",
    "UK"
]

for location in locations:
    print(location)
```

Data Engineering example:

```python
files = [
    "customers.csv",
    "orders.csv",
    "products.csv"
]

for file in files:
    print(f"Processing: {file}")
```

---

# 20. Loop Through Dictionaries

```python
customer = {
    "id": 101,
    "name": "Prince",
    "country": "India"
}

for key, value in customer.items():
    print(key, value)
```

Output:

```text
id 101
name Prince
country India
```

---

# 21. While Loop

A `while` loop runs while a condition is true.

```python
counter = 1

while counter <= 5:
    print(counter)
    counter += 1
```

Be careful with `while` loops because an incorrect condition can create an infinite loop.

---

# 22. Break

Stop a loop.

```python
for number in range(10):
    if number == 5:
        break

    print(number)
```

---

# 23. Continue

Skip the current iteration.

```python
for number in range(10):
    if number == 5:
        continue

    print(number)
```

---

# 24. Range

`range()` generates a sequence of numbers.

```python
for number in range(5):
    print(number)
```

Output:

```text
0
1
2
3
4
```

Another example:

```python
for number in range(1, 6):
    print(number)
```

---

# 25. Functions

Functions allow you to reuse logic.

```python
def calculate_total(price, quantity):
    return price * quantity


total = calculate_total(100, 5)

print(total)
```

Output:

```text
500
```

---

# 26. Function Parameters

```python
def greet(name):
    print(f"Hello {name}")


greet("Prince")
```

Multiple parameters:

```python
def create_customer(customer_id, name, country):
    return {
        "id": customer_id,
        "name": name,
        "country": country
    }


customer = create_customer(
    101,
    "Prince",
    "India"
)

print(customer)
```

---

# 27. Default Parameters

```python
def greet(name, country="India"):
    print(f"{name} is from {country}")


greet("Prince")
greet("John", "USA")
```

---

# 28. Lambda Functions

A lambda is a small anonymous function.

```python
square = lambda x: x * x

print(square(5))
```

Lambda functions are commonly used with:

```text
map()
filter()
sorted()
```

Don't overuse them. Regular functions are often easier to read.

---

# 29. List Comprehension

Normal approach:

```python
numbers = [1, 2, 3, 4, 5]

squares = []

for number in numbers:
    squares.append(number * number)

print(squares)
```

List comprehension:

```python
numbers = [1, 2, 3, 4, 5]

squares = [
    number * number
    for number in numbers
]

print(squares)
```

With a condition:

```python
numbers = [1, 2, 3, 4, 5, 6]

even_numbers = [
    number
    for number in numbers
    if number % 2 == 0
]

print(even_numbers)
```

---

# 30. Exception Handling

Data pipelines frequently encounter errors:

* Missing files
* Invalid data
* Database connection failures
* API failures
* Incorrect data types

Use `try` and `except`:

```python
try:
    number = int("abc")
except ValueError:
    print("Invalid number")
```

Using `finally`:

```python
try:
    print("Processing data")
except Exception as error:
    print(f"Error: {error}")
finally:
    print("Process completed")
```

Avoid blindly catching every exception without handling or logging it properly.

---

# 31. File Handling

Data Engineers frequently work with files.

## Read a file

```python
with open("data.txt", "r") as file:
    content = file.read()

print(content)
```

## Write a file

```python
with open("output.txt", "w") as file:
    file.write("Hello Data Engineering")
```

The `with` statement automatically closes the file.

---

# 32. CSV Files

Python provides the `csv` module.

```python
import csv

with open("customers.csv", "r") as file:
    reader = csv.DictReader(file)

    for row in reader:
        print(row)
```

Access columns:

```python
print(row["name"])
print(row["country"])
```

For larger data-processing tasks, we'll later use Pandas.

---

# 33. JSON

JSON is extremely common in APIs and Data Engineering pipelines.

```python
import json

customer = {
    "id": 101,
    "name": "Prince",
    "country": "India"
}
```

Convert Python dictionary to JSON:

```python
json_data = json.dumps(customer)

print(json_data)
```

Convert JSON back to Python:

```python
data = json.loads(json_data)

print(data["name"])
```

Read JSON from a file:

```python
with open("customer.json", "r") as file:
    data = json.load(file)

print(data)
```

Write JSON:

```python
with open("customer.json", "w") as file:
    json.dump(customer, file, indent=4)
```

---

# 34. Modules

A module is a Python file containing reusable code.

Example:

```text
python/
├── basics/
│   ├── calculations.py
│   └── main.py
```

`calculations.py`:

```python
def add(a, b):
    return a + b
```

`main.py`:

```python
from calculations import add

result = add(10, 20)

print(result)
```

Modules help organize larger Data Engineering applications.

---

# 35. Useful Standard Library Modules

## `os`

```python
import os

print(os.getcwd())
print(os.listdir("."))
```

## `pathlib`

Prefer `pathlib` for modern file-path handling.

```python
from pathlib import Path

data_directory = Path("datasets")

for file in data_directory.iterdir():
    print(file)
```

## `datetime`

```python
from datetime import datetime

current_time = datetime.now()

print(current_time)
```

## `json`

```python
import json
```

## `csv`

```python
import csv
```

---

# 36. Environment Variables

Never hardcode secrets:

```python
password = "my-password"
api_key = "secret-key"
```

Instead, use environment variables.

Linux:

```bash
export API_KEY="your-key"
```

Python:

```python
import os

api_key = os.getenv("API_KEY")

print(api_key)
```

For production systems, use a proper secret-management solution.

---

# 37. Virtual Environments

Create:

```bash
python3 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

Install packages:

```bash
pip install pandas
```

Check installed packages:

```bash
pip list
```

Save dependencies:

```bash
pip freeze > requirements.txt
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Deactivate:

```bash
deactivate
```

Do not commit `.venv` to Git.

Add to `.gitignore`:

```text
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
.env
```

---

# 38. Package Management

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install a package:

```bash
pip install pandas
```

Install a specific version:

```bash
pip install pandas==2.3.2
```

Uninstall:

```bash
pip uninstall pandas
```

Show packages:

```bash
pip list
```

---

# 39. Data Engineering Example

Consider this order data:

```python
orders = [
    {
        "order_id": 1001,
        "customer": "Prince",
        "amount": 500
    },
    {
        "order_id": 1002,
        "customer": "John",
        "amount": 1000
    },
    {
        "order_id": 1003,
        "customer": "David",
        "amount": 750
    }
]
```

Calculate total:

```python
total = 0

for order in orders:
    total += order["amount"]

print(total)
```

Output:

```text
2250
```

Filter orders above 700:

```python
large_orders = []

for order in orders:
    if order["amount"] > 700:
        large_orders.append(order)

print(large_orders)
```

This is the foundation of **data transformation**.

Later, the same concepts will be implemented using:

```text
Python
   ↓
Pandas
   ↓
PySpark
   ↓
Distributed Data Processing
```

---

# 40. Mini ETL Example

A basic ETL pipeline has three major stages:

```text
Extract
   ↓
Transform
   ↓
Load
```

Example:

```text
orders.json
     ↓
  Extract
     ↓
  Transform
     ↓
  Load
     ↓
processed_orders.json
```

Example implementation:

```python
import json


def extract(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def transform(orders):
    valid_orders = []

    for order in orders:
        if order["amount"] > 0:
            order["customer"] = order["customer"].strip().lower()
            valid_orders.append(order)

    return valid_orders


def load(orders, file_path):
    with open(file_path, "w") as file:
        json.dump(orders, file, indent=4)


orders = extract("datasets/orders.json")

processed_orders = transform(orders)

load(
    processed_orders,
    "datasets/processed_orders.json"
)
```

This is a very simple ETL pipeline, but the same pattern appears in larger systems.

---

# 41. Important Python Concepts for Data Engineering

Before moving to Pandas and PySpark, you should be comfortable with:

* Variables
* Data types
* Strings
* Lists
* Tuples
* Dictionaries
* Sets
* Conditions
* Loops
* Functions
* Lambda functions
* List comprehensions
* Exception handling
* File handling
* CSV
* JSON
* Modules
* Packages
* Virtual environments
* `os`
* `pathlib`
* `datetime`
* Environment variables
* Basic ETL concepts

---

# 42. Practice Exercises

## Exercise 1 — Customer

Create:

```python
customer = {
    "id": 101,
    "name": "Prince",
    "age": 25,
    "country": "India",
    "orders": [1001, 1002, 1003]
}
```

Print:

```text
Name:
Country:
Age:
Number of Orders:
Orders:
```

---

## Exercise 2 — Orders

Create:

```python
orders = [
    {"id": 1, "amount": 500},
    {"id": 2, "amount": 1200},
    {"id": 3, "amount": 800},
    {"id": 4, "amount": 200}
]
```

Calculate:

1. Total order amount
2. Number of orders
3. Average order amount
4. Largest order
5. Orders above 500

---

## Exercise 3 — Data Cleaning

Given:

```python
names = [
    " Prince ",
    "JOHN",
    " david ",
    "ALICE "
]
```

Create:

```text
[
    "prince",
    "john",
    "david",
    "alice"
]
```

Use:

```python
.strip()
.lower()
```

---

## Exercise 4 — File Processing

Create:

```text
datasets/customers.txt
```

Add several customer names.

Write Python code to:

1. Open the file
2. Read the data
3. Process each line
4. Remove whitespace
5. Print each customer

---

## Exercise 5 — JSON

Create:

```python
customer = {
    "id": 101,
    "name": "Prince",
    "country": "India",
    "skills": [
        "Python",
        "SQL",
        "PySpark"
    ]
}
```

Convert it to JSON and then convert it back into a Python dictionary.

---

# 43. Mini Project — Python ETL

Create:

```text
datasets/orders.json
```

Add several orders.

Build a Python pipeline that:

### Extract

Read the JSON file.

### Transform

Perform:

* Remove invalid orders
* Normalize customer names
* Filter orders
* Calculate totals
* Validate required fields

### Load

Write the processed data to:

```text
datasets/processed_orders.json
```

Final flow:

```text
orders.json
    │
    ▼
 Extract
    │
    ▼
 Transform
    ├── Clean
    ├── Validate
    ├── Filter
    └── Calculate
    │
    ▼
 Load
    │
    ▼
processed_orders.json
```

---

# 44. Python Basics Checklist

Before moving to Pandas, make sure you can confidently explain and use:

* [ ] Variables
* [ ] Data types
* [ ] Strings
* [ ] Numbers
* [ ] Lists
* [ ] Tuples
* [ ] Dictionaries
* [ ] Sets
* [ ] `None`
* [ ] Type conversion
* [ ] Conditions
* [ ] Logical operators
* [ ] `for` loops
* [ ] `while` loops
* [ ] `break`
* [ ] `continue`
* [ ] Functions
* [ ] Function parameters
* [ ] Default parameters
* [ ] Lambda functions
* [ ] List comprehensions
* [ ] Exception handling
* [ ] File handling
* [ ] CSV
* [ ] JSON
* [ ] Modules
* [ ] `os`
* [ ] `pathlib`
* [ ] `datetime`
* [ ] Environment variables
* [ ] Virtual environments
* [ ] Package management
* [ ] Basic ETL

---

# 45. Recommended Learning Sequence

Follow this sequence for your Data Engineering journey:

```text
01. Python Basics
        ↓
02. Python Data Structures
        ↓
03. Functions & Modules
        ↓
04. File Handling
        ↓
05. CSV & JSON
        ↓
06. Exception Handling
        ↓
07. Virtual Environments
        ↓
08. Python ETL Mini Project
        ↓
09. Pandas
        ↓
10. SQL
        ↓
11. PySpark
        ↓
12. Advanced PySpark
        ↓
13. ETL Pipelines
        ↓
14. Data Warehousing
        ↓
15. Data Lake / Lakehouse
        ↓
16. Delta Lake
        ↓
17. Databricks
        ↓
18. Structured Streaming
        ↓
19. Production Data Pipelines
        ↓
20. Data Engineering Projects
```

## Goal

The objective is not just to memorize Python syntax.

You should be able to take raw data:

```text
CSV / JSON / API / Database
            ↓
         Python
            ↓
       Clean & Validate
            ↓
        Transform
            ↓
          Load
            ↓
     Pandas / PySpark
            ↓
        Databricks
```

and understand **why, where, and how each technology is used**.
