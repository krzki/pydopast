# Pydopast

Pydopast is a library to build software product lines through Delta-Oriented Programming (DOP). 

### Why Pydopast

Pydopast perform modification on Python Abstract Syntax Tree (AST) directly, instead of resorting to dynamic modification at runtime, such as [Pydop](https://github.com/onera/pydop). This allows Pydopast to complately prevent side-effect form attributes and/or classes, which are going to be removed or modified.

### Installation

The required Python version for this library is <b>3.13 or higher</b>

1.  Clone Pydopast
    ```
    $ git clone https://github.com/krzki/pydopast
    ```
2. (Optional) Create a virtual environment
    ```
    $ python3 -m venv my_env
    $ source my_env/bin/activate
    ```
3. Install the dependencies
    ```
    $ pip install -r requirements.txt
    ```
