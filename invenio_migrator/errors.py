# class MigrationError(Exception):
#     """Exception indicating an error related to the action."""

#     def __init__(self, action: str, reason) -> None:
#         """Constructor.

#         :param action: The name of the action in question.
#         :param reason: Description of what went wrong.
#         """
#         self.action = action
#         self.reason = reason

#     def __str__(self):
#         """Return str(self)."""
#         return f"Error for action '{self.action}': {self.reason}"


# class MappingError(MigrationError):
#     """Exception indicating an error related to the mapping."""

#     def __init__(self, action: str, reason) -> None:
#         """Constructor.

#         :param action: The name of the action in question.
#         :param reason: Description of what went wrong.
#         """
#         action = action or "Mapping"
#         reason = reason or "Could not map the record successfully."
#         super().__init__(action, reason)
