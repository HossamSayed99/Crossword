import sys
from crossword import *
from collections import deque
from copy import deepcopy


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Looping over all variables
        for var in self.crossword.variables:
            words_to_remove = set()
            # Looping over all words in a variable's domain and removing any word whose length != variable's length
            for word in self.domains[var]:
                if len(word) != var.length:
                    words_to_remove.add(word)
            # Removing invalid words from the domain of x
            for word in words_to_remove:
                self.domains[var].remove(word)
        return

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        flag = False
        # Getting the overlap between x and y
        overlap = self.crossword.overlaps[x, y]
        # If no overlap, then no revision is required and return false
        if overlap == None:
            return False

        words_to_remove = set()
        # Loop over each word in x's domain
        for value1 in self.domains[x]:
            flag = False
            # If there exists a value in y's domain that can be a possible value for x's value, then we will not removie this word
            for value2 in self.domains[y]:
                # print(value1, value2)
                if(value1[overlap[0]] == value2[overlap[1]]):
                    flag = True
                    break

            if not flag:
                words_to_remove.add(value1)

        if len(words_to_remove) == 0:
            return False

        # remove the non-valid words from x's domain and returning true
        else:
            for word in words_to_remove:
                self.domains[x].remove(word)
            return True

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        q = deque()
        list_of_arcs = []

        # Adding all arcs to the list
        if arcs == None:
            for x in self.crossword.variables:
                for y in self.crossword.neighbors(x):
                    list_of_arcs.append((x, y))
        else:

            list_of_arcs = arcs

        # Initializing the queue
        for arc in list_of_arcs:
            q.append(arc)

        # Implementing the ac3 algorithm
        while(len(q) != 0):
            x, y = q.popleft()
            if self.revise(x, y):

                if len(self.domains[x]) == 0:
                    return False

                neighbors = self.crossword.neighbors(x)
                for neighbor in neighbors:
                    if neighbor == y:
                        continue
                    q.append((neighbor, x))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.crossword.variables:
            if var in assignment:
                continue
            else:
                return False

        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Checking that all values are unique
        if len(set(assignment.values())) != len(assignment.values()):
            return False

        for var in assignment:
            val = assignment[var]
            # Checking that each value is of a valid length
            if len(val) != var.length:
                return False
            # Checking that there is no onflicts between neighboring variables
            neighbors = self.crossword.neighbors(var)

            for neighbor in neighbors:
                if neighbor in assignment:
                    x, y = self.crossword.overlaps[var, neighbor]
                    if val[x] != assignment[neighbor][y]:
                        return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # A dictionary that holds the value in the var's domain as keys and the number of values ruled
        # out for neighboring unassigned vraiables as values
        values_to_eliminated_values = dict()

        for val in self.domains[var]:
            values_to_eliminated_values[val] = 0

        neighbors = self.crossword.neighbors(var)
        for x in self.domains[var]:
            for neighbor in neighbors:
                if neighbor in assignment:
                    continue
                i, j = self.crossword.overlaps[var, neighbor]
                for y in self.domains[neighbor]:
                    if x == y or x[i] != y[j]:
                        values_to_eliminated_values[x] += 1

        ret = sorted(values_to_eliminated_values.keys(), key=lambda val: values_to_eliminated_values[val])

        # print(values_to_eliminated_values, ret)

        return ret

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # A dictionary that holds the variables as keys, and their remaining values and
        # degree as values
        unassigned_variables = dict()

        for var in self.crossword.variables:
            if var not in assignment:
                unassigned_variables[var] = (len(self.domains[var]), -len(self.crossword.neighbors(var)))

        ret = sorted(unassigned_variables.keys(), key=lambda val: (unassigned_variables[val][0], unassigned_variables[val][1]))

        # print(assignment, unassigned_variables, ret)
        # print(ret)
        if (len(ret)):
            return ret[0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)
        values = self.order_domain_values(var, assignment)

        initial_var_domain = deepcopy(self.domains[var])
        initial_neighbors_domain = dict()
        for y in self.crossword.neighbors(var):
            initial_neighbors_domain[y] = deepcopy(self.domains[y])

        for val in values:
            assignment[var] = val
            if self.consistent(assignment):

                self.domains[var] = [val]

                arcs = []
                initial_neighbors_domain = dict()
                for y in self.crossword.neighbors(var):
                    arcs.append((y, var))

                if self.ac3(arcs) != False:
                    result = self.backtrack(assignment)
                    if result != None:
                        return result

                self.domains[var] = deepcopy(initial_var_domain)
                for y in self.crossword.neighbors(var):
                    self.domains[y] = deepcopy(initial_neighbors_domain[y])

            assignment.pop(var)

        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
