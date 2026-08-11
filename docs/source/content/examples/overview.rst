💡 Examples
===========

Welcome to the examples gallery! Here you can find practical code recipes and complete bot implementations showcasing various features of PyWa.

🤖 Full Example Bots
---------------------

Looking for something more complete than a code snippet? Pywa ships a gallery of full, ready-to-run example bots —
order taking, OTP verification, WhatsApp Flows, calls, groups, and more — in the
`examples <https://github.com/david-lev/pywa/tree/master/examples>`_ directory of the repository. Browse and
download them straight from the CLI, no cloning required:

.. code-block:: bash
    pywa new                            # Generate a basic echo-bot template
    pywa new examples                   # List the official example bots
    pywa new examples 02-order-bot      # Download one — ready to run with `pywa dev`

See the `CLI guide <../cli.html#browsing-and-downloading-example-bots>`_ for all the options (``--async``, ``--out``, ``--ref``).

--------------------

📝 Code Recipes
----------------

The rest of this page contains smaller, practical code recipes and snippets showcasing individual PyWa features.

.. note::

   Some of these examples use older patterns. For the latest recommended design patterns and best practices, please refer to the main guides (like `Get Started <../getting-started.html>`_ and `Handlers <../handlers/overview.html>`_).

.. toctree::
    template
    flows
    demo-bots
    message
    interactive
    media
    sign_up_flow
