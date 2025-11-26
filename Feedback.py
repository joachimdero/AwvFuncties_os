def feedback_fn(bericht, feedback=None):
    if feedback:  # QGIS feedback object
        try:
            feedback.pushInfo(bericht)
            return
        except AttributeError:
            pass
    try:
        from arcpy import AddMessage  # ArcGIS
        AddMessage(bericht)
    except ImportError:
        print(bericht)  # Standalone