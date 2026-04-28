Examples
========

Google style
------------

.. code-block:: python

   def add_user(name: str, age: int) -> None:
       """Add user.

       Args:
           name: User name.
           age: User age.
       """

reStructuredText style
----------------------

.. code-block:: python

   def add_user(name: str, age: int) -> None:
       """Add user.

       :param name: User name.
       :param age: User age.
       """

Attributes section
------------------

.. code-block:: python

   class User:
       """User model.

       Attributes:
           name: User name.
           age: User age.
       """