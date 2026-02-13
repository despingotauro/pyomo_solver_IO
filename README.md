## pyomo_solver_IO
Basic graphic interface to solve optimization problems based on pyomo.

This GUI is intended to streamline the modeling process for users who prefer a visual interface over scripting. Once the model is entered, the GUI will use supported solvers to find a solution.

<img width="502" height="639" alt="fig-GUI_1" src="https://github.com/user-attachments/assets/2224f238-0f5d-4c2b-a8ac-0893227c33c1" />

## Basic instructions
1. **Number of Variables:**  
   Enter an integer representing the number of decision variables.  
   *Example:* For variables \( x_1, x_2 \), enter `2`.

2. **Problem Category:**  
   Choose between `Linear` or `Non-Linear` depending on the nature of your objective function and constraints.

3. **Domain:**  
   Select the type of variables from the following options:


   | **Domain**              | **Description**                 |
   |-------------------------|---------------------------------|
   | `NonNegativeReals`     | All real numbers \( \geq 0 \)  |
   | `NonPositiveReals`     | All real numbers \( \leq 0 \)  |
   | `Reals`                | All real numbers               |
   | `PositiveReals`        | All real numbers \( > 0 \)     |
   | `NegativeReals`        | All real numbers \( < 0 \)     |
   | `Integers`             | All integers                   |
   | `NonNegativeIntegers`  | All integers \( \geq 0 \)      |
   | `PositiveIntegers`     | All integers \( > 0 \)         |
   | `Binary`               | Only 0 or 1                    |

4. **Direction (sense):**  
   Specify whether the problem is a `Minimize` or `Maximize` problem.

5. **Objective Function:**  
   Enter the objective using variable names `x1, x2, ...`

   Supported mathematical functions include:
   - `exp()`, `log()`, `sqrt()`, `sin()`, `cos()`, `tan()`, `abs()`
   - Multiplication: `*`
   - Power: `**`

   *Examples:*  
   `3*x1 + 2*x2`  
   `exp(x1) + x2**2`

6. **Constraints:**  
   Enter one constraint per line using the same variable names.

   *Examples:*
x1 + x2 <= 10
x1 - x2 >= 2

7. **Valid Constraint Operators:**  
Use one of the following:
- `<=` for less than or equal to
- `>=` for greater than or equal to
- `==` for equality constraints

---


