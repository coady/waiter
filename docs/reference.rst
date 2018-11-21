Reference
=============
.. automodule:: waiter

wait
^^^^^^^^^^^
.. autoclass:: wait

waiter
^^^^^^^^^^^
.. autoclass:: waiter.base.waiter
   :members:
   :special-members:
   :exclude-members: __weakref__, Stats

   .. attribute:: Stats

      `Stats`_ class attribute

   .. attribute:: stats

      `Stats`_ instance attribute

awaiter
^^^^^^^^^^^
.. autoclass:: waiter.awaiter.awaiter
   :show-inheritance:
   :members:
   :special-members:

   .. note:: Overloads for async coroutine functions.

suppress
^^^^^^^^^^^
.. autofunction:: suppress

first
^^^^^^^^^^^
.. autofunction:: first

Stats
^^^^^^^^^^^
.. autoclass:: waiter.base.Stats
   :show-inheritance:
   :members:
   :special-members:

   .. note:: The `Stats`_ interface is considered provisional.
      It can be customized by overriding at the class or instance level.
