class InsufficientCreditsError(Exception):
    """Ridicata cand utilizatorul nu are suficiente credite pentru un apel AI."""
    pass


class ModelNotAvailableError(Exception):
    """Ridicata cand modelul cerut nu e suportat sau nu are cheie API configurata."""
    pass