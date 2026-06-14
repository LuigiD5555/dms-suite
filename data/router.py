class DataRouter:
    """
    A router to control all database operations on models in the 'data' application.

    Methods
    -------
    db_for_read(model, **hints)
        Directs read operations for 'data' app models to 'enterprise_data' database.

    db_for_write(model, **hints)
        Directs write operations for 'data' app models to 'enterprise_data' database.

    allow_relation(obj1, obj2, **hints)
        Allows relations if either object belongs to the 'data' app.

    allow_migrate(db, app_label, model_name=None, **hints)
        Ensures that the 'data' app only appears in the 'enterprise_data' database.
    """

    @staticmethod
    def db_for_read(model, **hints):
        """
        Directs read operations for 'data' app models to 'enterprise_data' database.

        Parameters
        ----------
        model : Model
            The model class for which the database is being selected.
        hints : dict
            Additional information that may influence the database selection.

        Returns
        -------
        str or None
            The name of the database to use for read operations, or None if no routing is needed.
        """
        if model._meta.app_label == "data":
            return "enterprise_data"
        return None

    @staticmethod
    def db_for_write(model, **hints):
        """
        Directs write operations for 'data' app models to 'enterprise_data' database.

        Parameters
        ----------
        model : Model
            The model class for which the database is being selected.
        hints : dict
            Additional information that may influence the database selection.

        Returns
        -------
        str or None
            The name of the database to use for write operations, or None if no routing is needed.
        """
        if model._meta.app_label == "data":
            return "enterprise_data"
        return None

    @staticmethod
    def allow_relation(obj1, obj2, **hints):
        """
        Allows relations if either object belongs to the 'data' app.

        Parameters
        ----------
        obj1 : Model
            The first model instance involved in the relation.
        obj2 : Model
            The second model instance involved in the relation.
        hints : dict
            Additional information that may influence the relation allowance.

        Returns
        -------
        bool or None
            True if the relation is allowed, or None if no routing is needed.
        """
        if obj1._meta.app_label == "data" or obj2._meta.app_label == "data":
            return True
        return None

    @staticmethod
    def allow_migrate(db, app_label, model_name=None, **hints):
        """
        Ensures that the 'data' app only appears in the 'enterprise_data' database.

        Parameters
        ----------
        db : str
            The name of the database being migrated to.
        app_label : str
            The label of the application being migrated.
        model_name : str, optional
            The name of the model being migrated.
        hints : dict
            Additional information that may influence the migration allowance.

        Returns
        -------
        bool or None
            True if the migration is allowed, or None if no routing is needed.
        """
        if app_label == "data":
            return db == "enterprise_data"
        return None
