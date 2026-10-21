# Prepared AI outputs

These files hold responses in the style of an AI assistant. They were written for this workshop,
not generated during it, so that every pair has something to review when an assistant is slow,
blocked, or not available, and so that a pair that is ahead has something to challenge.

**None of them is correct as written.** Each one contains problems on purpose. Finding them is the
exercise: the same review that you give to any proposal, from a tool or from a colleague.

| File | For | How to use it |
|---|---|---|
| `Lab1_prepared_response_Genie_Code.md` | Lab 1, Tasks 1 to 3 | Review each response against the review questions of the notebook. Paste the code into the task cell, run the check, repair what it reports. |
| `Lab2_prepared_change_Copilot.md` | Lab 2, steps 2 and 3 | `python tools/checkpoint.py prepared lab2` writes the change over your files. Review it in the Source Control view, or with `python tools/checkpoint.py diff`. |
| `Lab3_prepared_test_cases.md` | Lab 3, step 1 | Decide for each proposed case: accept, reject, or already covered. Calculate the expected values yourself. |
| `Lab3_prepared_tests_and_checks.md` | Lab 3, steps 2 and 3 | `python tools/checkpoint.py prepared lab3`, then review and run. |
| `Lab3_prepared_fix_proposals.md` | Lab 3, step 5 | Three candidates for each cause. One corrects the cause. Decide which, and say why the others do not. |
| `Lab4_prepared_change.md` | Lab 4, step 3 | `python tools/checkpoint.py prepared lab4`, then review and run. Its summary says that all code tests pass. |

A prepared change is never committed and never run for you. After `prepared`, your working files
differ from the checkpoint exactly as if an assistant had edited them.

Say in your review note when you worked from a prepared output. A prepared output proves that you
can review. It does not prove that the assistant works on your workstation.
