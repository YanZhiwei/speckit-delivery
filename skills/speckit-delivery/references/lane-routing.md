# Lane routing

Choose Feature when the change introduces new behavior, crosses module ownership, changes a public contract, changes durable data, or requires an architectural decision. Promote a complex bug to Feature when its remediation meets any of those conditions.

Choose Bugfix when there is an observable defect, a bounded root-cause investigation, and a regression test can express the expected behavior.

Choose Lightweight when the outcome is mechanical, documentation-only, or behavior-preserving with a narrow credible verification command.

When uncertain between lanes, choose the more explicit lane until scope evidence justifies a downgrade.
