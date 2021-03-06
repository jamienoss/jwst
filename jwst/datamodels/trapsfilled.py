from .model_base import DataModel

__all__ = ['TrapsFilledModel']

class TrapsFilledModel(DataModel):
    """
    A data model for the number of traps filled for a detector, for
    persistence.

    Parameters
    ----------
    init: any
        Any of the initializers supported by `~jwst.datamodels.DataModel`.

    data: numpy array
        The map of the number of traps filled over the detector, with
        one plane for each "trap family."
    """
    schema_url = "trapsfilled.schema.yaml"
