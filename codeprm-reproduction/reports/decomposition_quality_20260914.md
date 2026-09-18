# M3 decomposition review pack

This pack is blind to public/private execution outcomes. For each problem, read the problem and its starter API, then inspect labels A and B without trying to guess which protocol produced them.

## Scoring

Give each criterion 0, 1, or 2 points: 0 = absent/wrong, 1 = partly usable, 2 = clear and complete. Score coverage, input/output contract, dependency clarity, independent implementability, and granularity. Write a short note for any 0 or 1.

After scoring both blind candidates, open the human template CSV and write your own proposed functions for every problem. Use at most four functions, keep the exact starter entrypoint as the last function, and state each dependency. Do not consult private results or generated implementations.

## apps-train-2658

### Problem

Complete the function to determine the number of bits required to convert integer `A` to integer `B` (where `A` and `B` >= 0)

The upper limit for `A` and `B` is 2^(16), `int.MaxValue` or similar.

For example, you can change 31 to 14 by flipping the 4th and 0th bit:
```
 31  0 0 0 1 1 1 1 1
 14  0 0 0 0 1 1 1 0
---  ---------------
bit  7 6 5 4 3 2 1 0
```
Thus `31` and `14` should return `2`.

### Starter API

```python
def convert_bits(a, b):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "calculate_bit_difference",
      "signature": "calculate_bit_difference(a, b)",
      "docstring": "Calculate the number of differing bits between two integers.",
      "depends_on": []
    },
    {
      "name": "count_set_bits",
      "signature": "count_set_bits(n)",
      "docstring": "Count the number of set bits (1s) in an integer.",
      "depends_on": [
        "calculate_bit_difference"
      ]
    },
    {
      "name": "convert_bits",
      "signature": "convert_bits(a, b)",
      "docstring": "Determine the number of bits required to convert integer A to integer B.",
      "depends_on": [
        "count_set_bits"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "count_differences",
      "signature": "count_differences(a, b)",
      "docstring": "Count the number of differing bits between two integers.\n\nParameters:\na (int): The first integer.\nb (int): The second integer.\n\nReturns:\nint: The number of differing bits.",
      "depends_on": []
    },
    {
      "name": "convert_bits",
      "signature": "convert_bits(a, b)",
      "docstring": "Determine the number of bits required to convert integer A to integer B.\n\nParameters:\na (int): The first integer.\nb (int): The second integer.\n\nReturns:\nint: The number of bits required to convert A to B.",
      "depends_on": [
        "count_differences"
      ]
    }
  ]
}
```

## apps-train-2661

### Problem

A marine themed rival site to Codewars has started. Codwars is advertising their website all over the internet using subdomains to hide or obfuscate their domain to trick people into clicking on their site.

Your task is to write a function that accepts a URL as a string and determines if it would result in an http request to codwars.com.

Function should return true for all urls in the codwars.com domain. All other URLs should return false.

The urls are all valid but may or may not contain http://, https:// at the beginning or subdirectories or querystrings at the end.

For additional confusion, directories in can be named "codwars.com" in a url with the codewars.com domain and vise versa. Also, a querystring may contain codewars.com or codwars.com for any other domain - it should still return true or false based on the domain of the URL and not the domain in the querystring. Subdomains can also add confusion: for example `http://codwars.com.codewars.com` is a valid URL in the codewars.com domain in the same way that `http://mail.google.com` is a valid URL within google.com

Urls will not necessarily have either codewars.com or codwars.com in them. The folks at Codwars aren't very good about remembering the contents of their paste buffers.

All urls contain domains with a single TLD; you need not worry about domains like company.co.uk.

```
findCodwars("codwars.com"); // true
findCodwars("https://subdomain.codwars.com/a/sub/directory?a=querystring"); // true
findCodwars("codewars.com"); // false
findCodwars("https://subdomain.codwars.codewars.com/a/sub/directory/codwars.com?a=querystring"); // false
```

### Starter API

```python
def find_codwars(url):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "parse_url",
      "signature": "parse_url(url: str) -> dict",
      "docstring": "Parses a URL into its components.",
      "depends_on": []
    },
    {
      "name": "is_codwars_domain",
      "signature": "is_codwars_domain(parsed_url: dict) -> bool",
      "docstring": "Determines if the parsed URL is in the codwars.com domain.",
      "depends_on": [
        "parse_url"
      ]
    },
    {
      "name": "find_codwars",
      "signature": "find_codwars(url: str) -> bool",
      "docstring": "Determines if the URL would result in an http request to codwars.com.",
      "depends_on": [
        "is_codwars_domain"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "is_valid_url",
      "signature": "is_valid_url(url)",
      "docstring": "Check if the given URL is valid.\n\nArgs:\nurl (str): The URL to check.\n\nReturns:\nbool: True if the URL is valid, False otherwise.",
      "depends_on": []
    },
    {
      "name": "extract_domain",
      "signature": "extract_domain(url)",
      "docstring": "Extract the domain from the given URL.\n\nArgs:\nurl (str): The URL from which to extract the domain.\n\nReturns:\nstr: The extracted domain.",
      "depends_on": [
        "is_valid_url"
      ]
    },
    {
      "name": "is_codwars_domain",
      "signature": "is_codwars_domain(domain)",
      "docstring": "Check if the given domain is a codwars.com domain.\n\nArgs:\ndomain (str): The domain to check.\n\nReturns:\nbool: True if the domain is a codwars.com domain, False otherwise.",
      "depends_on": [
        "is_valid_url",
        "extract_domain"
      ]
    },
    {
      "name": "find_codwars",
      "signature": "find_codwars(url)",
      "docstring": "Determine if the given URL would result in an http request to codwars.com.\n\nArgs:\nurl (str): The URL to check.\n\nReturns:\nbool: True if the URL is in the codwars.com domain, False otherwise.",
      "depends_on": [
        "is_valid_url",
        "extract_domain",
        "is_codwars_domain"
      ]
    }
  ]
}
```

## apps-train-2657

### Problem

In this exercise, a string is passed to a method and a new string has to be returned with the first character of each word in the string.

For example:

```
"This Is A Test" ==> "TIAT"
```

### Starter API

```python
def make_string(s):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "split_string",
      "signature": "split_string(s)",
      "docstring": "Splits the input string into a list of words.",
      "depends_on": []
    },
    {
      "name": "capitalize_words",
      "signature": "capitalize_words(words)",
      "docstring": "Capitalizes the first letter of each word in the list.",
      "depends_on": [
        "split_string"
      ]
    },
    {
      "name": "join_words",
      "signature": "join_words(capitalized_words)",
      "docstring": "Joins the list of capitalized words into a single string.",
      "depends_on": [
        "capitalize_words"
      ]
    },
    {
      "name": "make_string",
      "signature": "make_string(s)",
      "docstring": "Returns a new string with the first character of each word capitalized.",
      "depends_on": [
        "join_words"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "capitalize_first_char",
      "signature": "capitalize_first_char(word)",
      "docstring": "Capitalizes the first character of a given word.\n\nArgs:\nword (str): The word to capitalize.\n\nReturns:\nstr: The word with the first character capitalized.",
      "depends_on": []
    },
    {
      "name": "process_word",
      "signature": "process_word(word)",
      "docstring": "Processes a word to return its first character capitalized.\n\nArgs:\nword (str): The word to process.\n\nReturns:\nstr: The first character of the word capitalized.",
      "depends_on": [
        "capitalize_first_char"
      ]
    },
    {
      "name": "make_string",
      "signature": "make_string(s)",
      "docstring": "Converts a string to a new string with the first character of each word capitalized.\n\nArgs:\ns (str): The input string.\n\nReturns:\nstr: A new string with the first character of each word capitalized.",
      "depends_on": [
        "capitalize_first_char",
        "process_word"
      ]
    }
  ]
}
```

## apps-train-2656

### Problem

In the world of birding there are four-letter codes for the common names of birds. These codes are created by some simple rules:

* If the bird's name has only one word, the code takes the first four letters of that word. 
* If the name is made up of two words, the code takes the first two letters of each word.
* If the name is made up of three words, the code is created by taking the first letter from the first two words and the first two letters from the third word.
* If the name is four words long, the code uses the first letter from all the words.

*(There are other ways that codes are created, but this Kata will only use the four rules listed above)*

Complete the function that takes an array of strings of common bird names from North America, and create the codes for those names based on the rules above. The function should return an array of the codes in the same order in which the input names were presented.

Additional considertations:

* The four-letter codes  in the returned array should be in UPPER CASE.
* If a common name has a hyphen/dash, it should be considered a space. 

## Example

If the input array is: `["Black-Capped Chickadee", "Common Tern"]`

The return array would be: `["BCCH", "COTE"]`

### Starter API

```python
def bird_code(arr):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "clean_name",
      "signature": "clean_name(name)",
      "docstring": "Remove hyphens and convert to uppercase.",
      "depends_on": []
    },
    {
      "name": "split_name",
      "signature": "split_name(name)",
      "docstring": "Split the name into words.",
      "depends_on": [
        "clean_name"
      ]
    },
    {
      "name": "generate_code",
      "signature": "generate_code(words)",
      "docstring": "Generate the bird code based on the number of words.",
      "depends_on": [
        "clean_name",
        "split_name"
      ]
    },
    {
      "name": "bird_code",
      "signature": "bird_code(arr)",
      "docstring": "Generate bird codes for an array of bird names.",
      "depends_on": [
        "clean_name",
        "split_name",
        "generate_code"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "split_name",
      "signature": "split_name(name)",
      "docstring": "Splits the bird name into words, treating hyphens as spaces.",
      "depends_on": []
    },
    {
      "name": "create_code",
      "signature": "create_code(words)",
      "docstring": "Creates a four-letter code based on the number of words in the bird name.",
      "depends_on": [
        "split_name"
      ]
    },
    {
      "name": "bird_code",
      "signature": "bird_code(arr)",
      "docstring": "Generates four-letter codes for a list of bird names.",
      "depends_on": [
        "create_code"
      ]
    }
  ]
}
```

## apps-train-2652

### Problem

Your task is to write a function which counts the number of squares contained in an ASCII art picture.

The input pictures contain rectangles---some of them squares---drawn with the characters `-`, `|`, and `+`, where `-` and `|` are used to represent horizontal and vertical sides, and `+` is used to represent corners and intersections. Each picture may contain multiple, possibly overlapping, rectangles.

A simple example input looks like this:

    +--+  +----+
    |  |  |    |    +-+
    |  |  +----+    | |
    +--+            +-+
    
There are two squares and one rectangle in this picture, so your function should return 2 for this input.

The following picture does not contain any squares, so the answer for this one is 0:

    +------+
    |      |
    +------+

Here is another, more complex input:

    +---+
    |   |
    | +-+-+
    | | | |
    +-+-+ |
      |   |
      +---+

The answer for this one is 3: two big squares, and a smaller square formed by the intersection of the two bigger ones. Similarly, the answer for the following picture is 5:

    +-+-+
    | | |
    +-+-+
    | | |
    +-+-+

You are going to implement a function `count_squares()` which takes an ASCII art picture as input and returns the number of squares the picture shows. The input to that function is an array of strings, where each string corresponds to a line of the ASCII art picture. Each string is guaranteed to contain only the characters `-`, `|`, `+`, and `` `` (space).

The smallest valid square has a side length of 2 and is represented by four `+` characters arranged in a square; a single `+` character is not considered a square.

Have fun!

### Starter API

```python
def count_squares(lines):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "parse_grid",
      "signature": "parse_grid(lines)",
      "docstring": "Parses the input lines into a grid of characters.",
      "depends_on": []
    },
    {
      "name": "find_corners",
      "signature": "find_corners(grid)",
      "docstring": "Finds all the corner characters ('+') in the grid.",
      "depends_on": [
        "parse_grid"
      ]
    },
    {
      "name": "is_square",
      "signature": "is_square(grid, top_left, bottom_right)",
      "docstring": "Checks if the area defined by top_left and bottom_right is a square.",
      "depends_on": [
        "parse_grid"
      ]
    },
    {
      "name": "count_squares",
      "signature": "count_squares(lines)",
      "docstring": "Counts the number of squares in the ASCII art picture.",
      "depends_on": [
        "find_corners",
        "is_square"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "find_corners",
      "signature": "find_corners(lines)",
      "docstring": "Find all corners in the ASCII art picture.\n\nArgs:\nlines (list of str): The ASCII art picture as a list of strings.\n\nReturns:\nlist of tuple: A list of tuples representing the coordinates of corners.",
      "depends_on": []
    },
    {
      "name": "is_square",
      "signature": "is_square(lines, top_left, bottom_right)",
      "docstring": "Check if the area defined by top_left and bottom_right is a square.\n\nArgs:\nlines (list of str): The ASCII art picture as a list of strings.\ntop_left (tuple): The coordinates of the top-left corner.\nbottom_right (tuple): The coordinates of the bottom-right corner.\n\nReturns:\nbool: True if the area is a square, False otherwise.",
      "depends_on": [
        "find_corners"
      ]
    },
    {
      "name": "count_squares",
      "signature": "count_squares(lines)",
      "docstring": "Count the number of squares in the ASCII art picture.\n\nArgs:\nlines (list of str): The ASCII art picture as a list of strings.\n\nReturns:\nint: The number of squares in the picture.",
      "depends_on": [
        "find_corners",
        "is_square"
      ]
    }
  ]
}
```

## apps-train-2653

### Problem

For this game of `BINGO`, you will receive a single array of 10 numbers from 1 to 26 as an input. Duplicate numbers within the array are possible.

Each number corresponds to their alphabetical order letter (e.g. 1 = A. 2 = B, etc). Write a function where you will win the game if your numbers can spell `"BINGO"`. They do not need to be in the right order in the input array). Otherwise you will lose. Your outputs should be `"WIN"` or `"LOSE"` respectively.

### Starter API

```python
def bingo(array):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "is_valid_number",
      "signature": "is_valid_number(number)",
      "docstring": "Check if the number is within the valid range for BINGO.",
      "depends_on": []
    },
    {
      "name": "map_number_to_letter",
      "signature": "map_number_to_letter(number)",
      "docstring": "Convert a number to its corresponding letter.",
      "depends_on": [
        "is_valid_number"
      ]
    },
    {
      "name": "contains_all_letters",
      "signature": "contains_all_letters(array)",
      "docstring": "Check if the array contains all the letters of 'BINGO'.",
      "depends_on": [
        "is_valid_number",
        "map_number_to_letter"
      ]
    },
    {
      "name": "bingo",
      "signature": "bingo(array)",
      "docstring": "Determine if the input array can spell 'BINGO'.",
      "depends_on": [
        "is_valid_number",
        "map_number_to_letter",
        "contains_all_letters"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "map_numbers_to_letters",
      "signature": "map_numbers_to_letters(array)",
      "docstring": "Converts an array of numbers to their corresponding letters.",
      "depends_on": []
    },
    {
      "name": "check_for_bingo",
      "signature": "check_for_bingo(letters)",
      "docstring": "Checks if the given letters can form the word 'BINGO'.",
      "depends_on": [
        "map_numbers_to_letters"
      ]
    },
    {
      "name": "bingo",
      "signature": "bingo(array)",
      "docstring": "Determines if the input array contains the letters to form 'BINGO'.",
      "depends_on": [
        "check_for_bingo"
      ]
    }
  ]
}
```

## apps-train-2668

### Problem

Step through my `green glass door`.

You can take the `moon`, but not the `sun`.

You can take your `slippers`, but not your `sandals`.

You can go through `yelling`, but not `shouting`.

You can't run through `fast`, but you can run with `speed`.

You can take a `sheet`, but not your `blanket`.

You can wear your `glasses`, but not your `contacts`.

Have you figured it out? Good! Then write a program that can figure it out as well.

### Starter API

```python
def step_through_with(s):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "can_take",
      "signature": "can_take(item)",
      "docstring": "Determine if the item can be taken.\n\nArgs:\nitem (str): The item to check.\n\nReturns:\nbool: True if the item can be taken, False otherwise.",
      "depends_on": []
    },
    {
      "name": "can_go_through",
      "signature": "can_go_through(action)",
      "docstring": "Determine if the action can be taken through the door.\n\nArgs:\naction (str): The action to check.\n\nReturns:\nbool: True if the action can be taken through the door, False otherwise.",
      "depends_on": [
        "can_take"
      ]
    },
    {
      "name": "can_run_through",
      "signature": "can_run_through(speed)",
      "docstring": "Determine if running through the door is possible at the given speed.\n\nArgs:\nspeed (str): The speed to check.\n\nReturns:\nbool: True if running through the door is possible at the given speed, False otherwise.",
      "depends_on": [
        "can_take",
        "can_go_through"
      ]
    },
    {
      "name": "step_through_with",
      "signature": "step_through_with(s)",
      "docstring": "Step through the green glass door based on the given constraints.\n\nArgs:\ns (str): The input string containing actions and items.\n\nReturns:\nstr: The result of stepping through the door.",
      "depends_on": [
        "can_take",
        "can_go_through",
        "can_run_through"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "is_valid_action",
      "signature": "is_valid_action(action, item)",
      "docstring": "Check if the given action can be performed with the item.",
      "depends_on": []
    },
    {
      "name": "can_take",
      "signature": "can_take(item)",
      "docstring": "Determine if the item can be taken.",
      "depends_on": [
        "is_valid_action"
      ]
    },
    {
      "name": "can_go_through",
      "signature": "can_go_through(action)",
      "docstring": "Determine if the action can be used to go through something.",
      "depends_on": [
        "is_valid_action"
      ]
    },
    {
      "name": "step_through_with",
      "signature": "step_through_with(s)",
      "docstring": "Step through the given string following the rules.",
      "depends_on": [
        "can_take",
        "can_go_through"
      ]
    }
  ]
}
```

## apps-train-2671

### Problem

You will be given a string (x) featuring a cat 'C', a dog 'D' and a mouse 'm'. The rest of the string will be made up of '.'. 

You need to find out if the cat can catch the mouse from it's current position. The cat can jump (j) characters. 

Also, the cat cannot jump over the dog.

So:

if j = 5:

```..C.....m.``` returns 'Caught!'  <-- not more than j characters between

```.....C............m......``` returns 'Escaped!'  <-- as there are more than j characters between the two, the cat can't jump far enough

if j = 10:

```...m.........C...D``` returns 'Caught!' <--Cat can jump far enough and jump is not over dog

```...m....D....C.......``` returns 'Protected!' <-- Cat can jump far enough, but dog is in the way, protecting the mouse

Finally, if all three animals are not present, return 'boring without all three'

### Starter API

```python
def cat_mouse(x,j):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "find_animals",
      "signature": "find_animals(x: str) -> dict",
      "docstring": "Finds the positions of the cat, dog, and mouse in the string.",
      "depends_on": []
    },
    {
      "name": "is_valid_position",
      "signature": "is_valid_position(x: str, cat_pos: int, dog_pos: int, mouse_pos: int) -> bool",
      "docstring": "Checks if the positions of the cat, dog, and mouse are valid.",
      "depends_on": [
        "find_animals"
      ]
    },
    {
      "name": "can_cat_jump_over_dog",
      "signature": "can_cat_jump_over_dog(cat_pos: int, dog_pos: int, jump: int) -> bool",
      "docstring": "Checks if the cat can jump over the dog.",
      "depends_on": []
    },
    {
      "name": "cat_mouse",
      "signature": "cat_mouse(x: str, j: int) -> str",
      "docstring": "Determines if the cat can catch the mouse.",
      "depends_on": [
        "find_animals",
        "is_valid_position",
        "can_cat_jump_over_dog"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "find_cat_position",
      "signature": "find_cat_position(x)",
      "docstring": "Finds the position of the cat in the string.\n\nParameters:\nx (str): The input string containing 'C', 'D', and 'm'.\n\nReturns:\nint: The index of the cat in the string, or -1 if not found.",
      "depends_on": []
    },
    {
      "name": "find_mouse_position",
      "signature": "find_mouse_position(x)",
      "docstring": "Finds the position of the mouse in the string.\n\nParameters:\nx (str): The input string containing 'C', 'D', and 'm'.\n\nReturns:\nint: The index of the mouse in the string, or -1 if not found.",
      "depends_on": [
        "find_cat_position"
      ]
    },
    {
      "name": "find_dog_position",
      "signature": "find_dog_position(x)",
      "docstring": "Finds the position of the dog in the string.\n\nParameters:\nx (str): The input string containing 'C', 'D', and 'm'.\n\nReturns:\nint: The index of the dog in the string, or -1 if not found.",
      "depends_on": [
        "find_cat_position",
        "find_mouse_position"
      ]
    },
    {
      "name": "cat_mouse",
      "signature": "cat_mouse(x, j)",
      "docstring": "Determines if the cat can catch the mouse.\n\nParameters:\nx (str): The input string containing 'C', 'D', and 'm'.\nj (int): The number of characters the cat can jump.\n\nReturns:\nstr: 'Caught!', 'Escaped!', 'Protected!', or 'boring without all three'.",
      "depends_on": [
        "find_cat_position",
        "find_mouse_position",
        "find_dog_position"
      ]
    }
  ]
}
```

## apps-train-2664

### Problem

In this Kata, you will check if it is possible to convert a string to a palindrome by changing one character. 

For instance:
```Haskell
solve ("abbx") = True, because we can convert 'x' to 'a' and get a palindrome. 
solve ("abba") = False, because we cannot get a palindrome by changing any character. 
solve ("abcba") = True. We can change the middle character. 
solve ("aa") = False 
solve ("ab") = True
```

Good luck!

Please also try [Single Character Palindromes](https://www.codewars.com/kata/5a2c22271f7f709eaa0005d3)

### Starter API

```python
def solve(s):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "is_palindrome",
      "signature": "is_palindrome(s)",
      "docstring": "Check if a string is a palindrome.\n\nArgs:\ns (str): The string to check.\n\nReturns:\nbool: True if the string is a palindrome, False otherwise.",
      "depends_on": []
    },
    {
      "name": "count_mismatches",
      "signature": "count_mismatches(s)",
      "docstring": "Count the number of mismatches between the first and last characters of a string.\n\nArgs:\ns (str): The string to check.\n\nReturns:\nint: The number of mismatches.",
      "depends_on": [
        "is_palindrome"
      ]
    },
    {
      "name": "solve",
      "signature": "solve(s)",
      "docstring": "Check if it is possible to convert a string to a palindrome by changing one character.\n\nArgs:\ns (str): The string to check.\n\nReturns:\nbool: True if it is possible to convert the string to a palindrome by changing one character, False otherwise.",
      "depends_on": [
        "is_palindrome",
        "count_mismatches"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "is_palindrome",
      "signature": "is_palindrome(s: str) -> bool",
      "docstring": "Check if the given string is a palindrome.",
      "depends_on": []
    },
    {
      "name": "count_mismatches",
      "signature": "count_mismatches(s: str) -> int",
      "docstring": "Count the number of characters that need to be changed to make the string a palindrome.",
      "depends_on": [
        "is_palindrome"
      ]
    },
    {
      "name": "solve",
      "signature": "solve(s: str) -> bool",
      "docstring": "Check if it is possible to convert the string to a palindrome by changing one character.",
      "depends_on": [
        "count_mismatches"
      ]
    }
  ]
}
```

## apps-train-2654

### Problem

Kate and Michael want to buy a pizza and share it. Depending on the price of the pizza, they are going to divide the costs:

* If the pizza is less than €5,- Michael invites Kate, so Michael pays the full price.
* Otherwise Kate will contribute 1/3 of the price, but no more than €10 (she's broke :-) and Michael pays the rest.

How much is Michael going to pay? Calculate the amount with two decimals, if necessary.

### Starter API

```python
def michael_pays(costs):
```

### Candidate A

```json
{
  "functions": [
    {
      "name": "calculate_kate_contribution",
      "signature": "calculate_kate_contribution(price)",
      "docstring": "Calculate Kate's contribution to the pizza cost.",
      "depends_on": []
    },
    {
      "name": "calculate_michael_payment",
      "signature": "calculate_michael_payment(price, kate_contribution)",
      "docstring": "Calculate how much Michael will pay for the pizza.",
      "depends_on": [
        "calculate_kate_contribution"
      ]
    },
    {
      "name": "michael_pays",
      "signature": "michael_pays(costs)",
      "docstring": "Calculate the amount Michael will pay for the pizza.",
      "depends_on": [
        "calculate_michael_payment"
      ]
    }
  ]
}
```

### Candidate B

```json
{
  "functions": [
    {
      "name": "calculate_kate_contribution",
      "signature": "calculate_kate_contribution(price)",
      "docstring": "Calculate Kate's contribution to the pizza cost.\n\nArgs:\nprice (float): The total price of the pizza.\n\nReturns:\nfloat: Kate's contribution, capped at €10.",
      "depends_on": []
    },
    {
      "name": "calculate_michael_payment",
      "signature": "calculate_michael_payment(price, kate_contribution)",
      "docstring": "Calculate Michael's payment for the pizza.\n\nArgs:\nprice (float): The total price of the pizza.\nkate_contribution (float): Kate's contribution to the pizza cost.\n\nReturns:\nfloat: Michael's payment for the pizza.",
      "depends_on": [
        "calculate_kate_contribution"
      ]
    },
    {
      "name": "michael_pays",
      "signature": "michael_pays(costs)",
      "docstring": "Calculate how much Michael is going to pay for the pizza.\n\nArgs:\ncosts (float): The total price of the pizza.\n\nReturns:\nfloat: Michael's payment for the pizza, rounded to two decimal places.",
      "depends_on": [
        "calculate_kate_contribution",
        "calculate_michael_payment"
      ]
    }
  ]
}
```
