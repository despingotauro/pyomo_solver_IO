import os,sys
import subprocess
import re

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from pyomo.environ import *


#stream that avoids glpk to crash
class DummyStream:
    def write(self, *args, **kwargs):
        pass
    def flush(self):
        pass

#safe math functions
SAFE_MATH_FUNCS = {
    'exp': exp,
    'log': log,
    'sqrt': sqrt,
    'sin': sin,
    'cos': cos,
    'tan': tan,
    'abs': abs
}

#getting the path of each solver .exe
def get_solver_path(name="glpsol.exe"):
    if getattr(sys, 'frozen', False):
        # PyInstaller frozen .exe
        base_path = sys._MEIPASS  # folder where bundled files live
    else:
        # normal Python run
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "solvers", name)

def get_solver_path2(name="ipopt.exe"):
    if getattr(sys, 'frozen', False):
        # PyInstaller frozen .exe
        base_path = sys._MEIPASS  # folder where bundled files live
    else:
        # normal Python run
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "solvers", name)

#time out to avoid frozen app to crash glpk
def patched_subprocess_run(*args, **kwargs):
    if kwargs.get("timeout") is not None:
        kwargs["timeout"] = 30
    return orig_subprocess_run(*args, **kwargs)

orig_subprocess_run = subprocess.run
subprocess.run = patched_subprocess_run

class LPMaxMinSolver(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimization Solver")
        self.setGeometry(200, 200, 500, 450)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # --- Create the Help button ---
        # Help button
        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(self.show_help)
        layout.addWidget(self.help_btn)
        # --- Connect to a function that shows the dialog ---
        # About button
        self.about_btn = QPushButton("About")
        self.about_btn.clicked.connect(self.show_about)
        layout.addWidget(self.about_btn)
        
        # Number of variables
        layout.addWidget(QLabel("Number of variables:"))
        self.var_entry = QLineEdit()
        layout.addWidget(self.var_entry)

        # Problem type selector: Linear / Non-Linear
        layout.addWidget(QLabel("Problem category:"))
        self.problem_type_selector = QComboBox()
        self.problem_type_selector.addItems(["Linear", "Non-Linear"])
        layout.addWidget(self.problem_type_selector)
        
        # Variable domain selector
        layout.addWidget(QLabel("Variable domain:"))
        self.domain_selector = QComboBox()
        self.domain_selector.addItems([
            "Reals",
            "NonNegativeReals (xi >= 0)",
            "NegativeReals (xi <= 0)",
            "Integers",
            "NonNegativeIntegers (xi >= 0)",
            "NonPositiveIntegers (xi <= 0)",
            "Binary"
        ])
        layout.addWidget(self.domain_selector)       
        
        # Max/Min selector
        layout.addWidget(QLabel("Direction:"))
        self.opt_selector = QComboBox()
        self.opt_selector.addItems(["Minimize", "Maximize"])
        layout.addWidget(self.opt_selector)

        # Objective input
        layout.addWidget(QLabel("Objective function (use x1, x2, ...):"))
        self.obj_entry = QLineEdit()
        layout.addWidget(self.obj_entry)

        # Constraints input
        layout.addWidget(QLabel("Constraints (one per line, use x1, x2, ...):"))
        self.cons_entry = QTextEdit()
        layout.addWidget(self.cons_entry)

        # Solve button
        solve_btn = QPushButton("Solve")
        solve_btn.clicked.connect(self.solve_problem)
        layout.addWidget(solve_btn)

        # Output label
        self.output_label = QLabel("")
        layout.addWidget(self.output_label)

        self.setLayout(layout)
    def show_help(self):
         help_text = """
         Basic instructions to enter the model:

         1. Number of variables: Enter an integer corresponding to the number of variables. Example x1,x2 corresponds to 2 variables
         2. Problem category: Linear or Non-Linear
         3. Domain: Select variable type (Reals, NonNegativeReals, Integers, etc.)
         4. Direction: Sense of the problem -> Minimize or Maximize
         5. Objective function: Use variable names x1, x2, ... Admisible math functions:
            - exp(), log(), sqrt(), sin(), cos(), tan(), abs()
            - multiplication (*)
            - power (**)
            Example: 3*x1 + 2*x2 or exp(x1) + x2**2
         6. Constraints: One per line, using the same variable names.
            Example: x1 + x2 <= 10
                         x1 - x2 >= 2
         7. Valid constraints: <=, >= or == (equality constraints)                
         
        """
         QMessageBox.information(self, "Model Help", help_text)
    
    #about button show
    def show_about(self):
         about_text = """
         <b>About:</b><br><br>
         Javier Quintero<br>
         Released 2025/08/27<br>
         v1.00<br><br>
         <b>Know me:</b> <a href='https://gestion2.urjc.es/pdi/public/ver/javier.quintero'>javier.quintero</a><br>
         <b>License:</b> <a href='https://creativecommons.org/licenses/by-sa/4.0/deed.es'>CC BY-SA 4.0</a>
         """
         msg = QMessageBox(self)
         msg.setWindowTitle("About")
         msg.setTextFormat(Qt.RichText)  # enable HTML formatting
         msg.setText(about_text)
         msg.setStandardButtons(QMessageBox.Ok)
         msg.exec()
         
    def solve_problem(self):
        # Save real stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = DummyStream()
            sys.stderr = DummyStream()
    
            # --- 1. Check number of variables ---
            try:
                num_vars = int(self.var_entry.text())
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Number of variables must be an integer.")
                return
    
            obj_expr = self.obj_entry.text()
            cons_text = self.cons_entry.toPlainText().strip().split("\n")
            problem_type = self.opt_selector.currentText()
    
            # --- 2. Define model ---
            model = ConcreteModel()
    
            # Map selection to Pyomo domain
            domain_choice = self.domain_selector.currentText()
            domain_map = {
                "Reals": Reals,
                "NonNegativeReals (xi >= 0)": NonNegativeReals,
                "NegativeReals (xi <= 0)": NegativeReals,
                "Integers": Integers,
                "NonNegativeIntegers (xi >= 0)": NonNegativeIntegers,
                "NonPositiveIntegers (xi <= 0)": NonPositiveIntegers,
                "Binary": Binary
            }
            var_domain = domain_map[domain_choice]
    
            for i in range(1, num_vars + 1):
                setattr(model, f"x{i}", Var(within=var_domain))
    
            # Prepare local dict for eval: model variables + safe math functions
            local_dict = {f"x{i}": getattr(model, f"x{i}") for i in range(1, num_vars + 1)}
            local_dict.update(SAFE_MATH_FUNCS)
    
            # --- 3. Evaluate objective safely ---
            try:
                # --- New Check: ensure variables in objective match num_vars ---
                import re
                vars_in_expr = set(re.findall(r'x\d+', obj_expr))
                max_var_index = max([int(v[1:]) for v in vars_in_expr], default=0)
                if max_var_index > num_vars:
                    QMessageBox.warning(
                        self,
                        "Input Error",
                        f"The objective function uses x{max_var_index}, "
                        f"but you specified only {num_vars} variables."
                    )
                    return
    
                sense = minimize if problem_type == "Minimize" else maximize
                model.obj = Objective(expr=eval(obj_expr, {"__builtins__": None}, local_dict), sense=sense)
            except Exception as e:
                QMessageBox.warning(self, "Input Error", f"Invalid objective function:\n{e}")
                return
    
            # --- 4. Evaluate constraints safely ---
            for i, con in enumerate(cons_text):
                if con.strip():
                    # --- New check: ensure constraint variables match num_vars ---
                    vars_in_con = set(re.findall(r'x\d+', con))
                    if vars_in_con:
                        max_var_index = max([int(v[1:]) for v in vars_in_con])
                        if max_var_index > num_vars:
                            QMessageBox.warning(
                                self,
                                "Input Error",
                                f"Constraint on line {i+1} uses x{max_var_index}, "
                                f"but you specified only {num_vars} variables."
                            )
                            return
                    # Evaluate safely
                    try:
                        setattr(model, f"con{i}", Constraint(expr=eval(con, {"__builtins__": None}, local_dict)))
                    except Exception as e:
                        QMessageBox.warning(self, "Input Error", f"Invalid constraint on line {i+1}:\n{e}")
                        return
    
            # --- 5. Solver selection ---
            problem_category = self.problem_type_selector.currentText()
            if problem_category == "Linear":
                solver = SolverFactory('glpk', executable=get_solver_path("glpsol.exe"))
                solver.options['tmlim'] = 30
            else:
                solver = SolverFactory('ipopt', executable=get_solver_path2("ipopt.exe"))
    
            # --- 6. Solve ---
            result = solver.solve(model, tee=False)
    
            # --- 7. Check solver status ---
            if result.solver.termination_condition == TerminationCondition.unbounded:
                self.output_label.setText("The problem is unbounded!")
                return
            elif result.solver.termination_condition != TerminationCondition.optimal:
                self.output_label.setText(f"Solver did not find an optimal solution.\nStatus: {result.solver.status}")
                return
    
            # --- 8. Display results ---
            output = ""
            for i in range(1, num_vars + 1):
                output += f"x{i} = {getattr(model, f'x{i}')():.2f}\n"
            output += f"{problem_type} Objective = {model.obj():.2f}"
            self.output_label.setText(output)
    
        finally:
            # Restore real stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
      


if __name__ == "__main__":
    # Reuse existing QApplication if present
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = LPMaxMinSolver()
    window.show()

    # Only call exec_() if a new app was created
    if not QApplication.instance().startingUp():
        sys.exit(app.exec_())
