import os
import re
import six
import glob
import ntpath

from django.conf import settings
from geoserver.catalog import Catalog, FailedRequestError
from geoserver.resource import FeatureType, Coverage
from geoserver.store import CoverageStore, DataStore, datastore_from_index, \
    coveragestore_from_index, wmsstore_from_index
from geoserver.support import DimensionInfo
from geoserver.workspace import Workspace
from geoserver.catalog import ConflictingDataError, UploadError

shp_exts = ['.shp', ]
csv_exts = ['.csv']
kml_exts = ['.kml']
xml_exts = ['.xml', '.gml']
json_exts = ['.json', '.geojson']

vec_exts = shp_exts + csv_exts + kml_exts + xml_exts
cov_exts = ['.tif', '.tiff', '.geotiff', '.geotif', '.asc', '.kmz']

SUPPORTED_EXTS = vec_exts + cov_exts

GEOSERVER_LAYER_TYPES = {
    'vector': FeatureType.resource_type,
    'raster': Coverage.resource_type,
}

gs_catalog = Catalog(
    settings.OGC_SERVER.get('url'),
    settings.OGC_SERVER.get('user'),
    settings.OGC_SERVER.get('password'),
    retries=settings.OGC_SERVER.get('MAX_RETRIES'),
    backoff_factor=settings.OGC_SERVER.get('BACKOFF_FACTOR')
)


def get_files(src_path):
    """Converts the data to Shapefiles or Geotiffs and returns
       a dictionary with all the required files
    """
    files = {}
    filename = None
    # We need to iterate files as filename could be the zipfile
    for item in os.listdir(src_path):
        item_basename, item_ext = ntpath.splitext(item)
        if item_ext.lower() in SUPPORTED_EXTS:
            filename = os.path.join(src_path, item)
            break

    # Make sure the file exists.
    if not os.path.exists(filename):
        msg = ('Could not open %s. Make sure you are using a '
               'valid file' % filename)
        raise Exception(msg)

    base_name, extension = os.path.splitext(filename)
    # Replace special characters in filenames - []{}()
    glob_name = re.sub(r'([\[\]\(\)\{\}])', r'[\g<1>]', base_name)
    if extension.lower() == '.shp':
        required_extensions = dict(
            shp='.[sS][hH][pP]', dbf='.[dD][bB][fF]', shx='.[sS][hH][xX]')
        for ext, pattern in required_extensions.items():
            matches = glob.glob(glob_name + pattern)
            if len(matches) == 0:
                msg = ('Expected helper file %s does not exist; a Shapefile '
                       'requires helper files with the following extensions: '
                       '%s') % (base_name + "." + ext,
                                list(required_extensions.keys()))
                raise Exception(msg)
            elif len(matches) > 1:
                msg = ('Multiple helper files for %s exist; they need to be '
                       'distinct by spelling and not just case.') % filename
                raise Exception(msg)
            else:
                files[ext] = matches[0]

        matches = glob.glob(glob_name + ".[pP][rR][jJ]")
        if len(matches) == 1:
            files['prj'] = matches[0]
        elif len(matches) > 1:
            msg = ('Multiple helper files for %s exist; they need to be '
                   'distinct by spelling and not just case.') % filename
            raise Exception(msg)

    elif extension.lower() in cov_exts:
        files[extension.lower().replace('.', '')] = filename

    matches = glob.glob(os.path.dirname(glob_name) + "/*.[sS][lL][dD]")
    if len(matches) == 1:
        files['sld'] = matches[0]
    elif len(matches) > 1:
        msg = ('Multiple style files (sld) for %s exist; they need to be '
                'distinct by spelling and not just case.') % filename
        raise Exception(msg)

    matches = glob.glob(glob_name + ".[xX][mM][lL]")

    # shapefile XML metadata is sometimes named base_name.shp.xml
    # try looking for filename.xml if base_name.xml does not exist
    if len(matches) == 0:
        matches = glob.glob(filename + ".[xX][mM][lL]")

    if len(matches) == 1:
        files['xml'] = matches[0]
    elif len(matches) > 1:
        msg = ('Multiple XML files for %s exist; they need to be '
               'distinct by spelling and not just case.') % filename
        raise Exception(msg)

    return files


def get_store(cat, name, workspace=None):
    # Make sure workspace is a workspace object and not a string.
    # If the workspace does not exist, continue as if no workspace had been defined.
    if isinstance(workspace, six.string_types):
        workspace = cat.get_workspace(workspace)

    if workspace is None:
        workspace = cat.get_default_workspace()

    if workspace:
        try:
            store = cat.get_xml('%s/%s.xml' %
                                (workspace.datastore_url[:-4], name))
        except FailedRequestError:
            try:
                store = cat.get_xml('%s/%s.xml' %
                                    (workspace.coveragestore_url[:-4], name))
            except FailedRequestError:
                try:
                    store = cat.get_xml('%s/%s.xml' %
                                        (workspace.wmsstore_url[:-4], name))
                except FailedRequestError:
                    raise FailedRequestError("No store found named: " + name)
        if store:
            if store.tag == 'dataStore':
                store = datastore_from_index(cat, workspace, store)
            elif store.tag == 'coverageStore':
                store = coveragestore_from_index(cat, workspace, store)
            elif store.tag == 'wmsStore':
                store = wmsstore_from_index(cat, workspace, store)

            return store
        else:
            raise FailedRequestError("No store found named: " + name)
    else:
        raise FailedRequestError("No store found named: " + name)


def create_featurestore(name, data, overwrite=False, charset="UTF-8", workspace=None):
    cat = gs_catalog
    try:
        cat.create_featurestore(
            name, data, overwrite=overwrite, charset=charset)
    except Exception as e:
        raise e
    store = get_store(cat, name, workspace=workspace)
    return store, cat.get_resource(name=name, store=store, workspace=workspace)


def create_coveragestore(name, data, overwrite=False, charset="UTF-8", workspace=None):
    cat = gs_catalog
    try:
        cat.create_coveragestore(
            name, path=data, overwrite=overwrite, upload_data=True)
    except Exception as e:
        raise e
    store = get_store(cat, name, workspace=workspace)
    return store, cat.get_resource(name=name, store=store, workspace=workspace)


def upload_to_geoserver(layer_name, layer_type, files, base_file, charset='UTF-8', overwrite=True, workspace=None):

    # Get workspace by name instead of get default one.
    workspace = gs_catalog.get_workspace(workspace)

    if layer_type == 'VECTOR':
        print(f'Uploading vector layer: [{base_file}]')
        create_store_and_resource = create_featurestore
    elif layer_type == 'RASTER':
        print(f'Uploading raster layer: [{base_file}]')
        create_store_and_resource = create_coveragestore
    else:
        msg = ('The layer type for name %s is %s. It should be '
               '%s or %s,' % (layer_name,
                              layer_type,
                              'VECTOR',
                              'RASTER'))
        raise Exception(msg)

    data = files
    if 'shp' not in files:
        data = base_file
    try:
        store, gs_resource = create_store_and_resource(
            layer_name,
            data,
            charset=charset,
            overwrite=overwrite,
            workspace=workspace)
    except UploadError as e:
        msg = ('Could not save the layer %s, there was an upload '
               'error: %s' % (layer_name, str(e)))
        e.args = (msg,)
        raise
    except ConflictingDataError as e:
        # A datastore of this name already exists
        msg = ('GeoServer reported a conflict creating a store with name %s: '
               '"%s". This should never happen because a brand new name '
               'should have been generated. But since it happened, '
               'try renaming the file or deleting the store in '
               'GeoServer.' % (layer_name, str(e)))
        e.args = (msg,)
        raise
    else:
        print(f'Finished upload of [{layer_name}] to GeoServer without errors.')

    # Verify the resource was created
    if not gs_resource:
        gs_resource = gs_catalog.get_resource(
            name=layer_name,
            workspace=workspace)

    if not gs_resource:
        msg = ('GeoNode encountered problems when creating layer %s.'
               'It cannot find the Layer that matches this Workspace.'
               'try renaming your files.' % layer_name)
        raise Exception(msg)

    assert gs_resource.name == layer_name

    # Make sure our data always has a valid projection
    _native_bbox = None
    try:
        _native_bbox = gs_resource.native_bbox
    except Exception:
        pass

    if _native_bbox and len(_native_bbox) >= 5 and _native_bbox[4:5][0] == 'EPSG:4326':
        box = _native_bbox[:4]
        minx, maxx, miny, maxy = [float(a) for a in box]
        if -180 <= round(minx, 5) <= 180 and -180 <= round(maxx, 5) <= 180 and \
                -90 <= round(miny, 5) <= 90 and -90 <= round(maxy, 5) <= 90:
            gs_resource.latlon_bbox = _native_bbox
            gs_resource.projection = "EPSG:4326"
        else:
            print(f'BBOX coordinates outside normal EPSG:4326 values for layer [{layer_name}].')
            _native_bbox = [-180, -90, 180, 90, "EPSG:4326"]
            gs_resource.latlon_bbox = _native_bbox
            gs_resource.projection = "EPSG:4326"
            print(f'BBOX coordinates forced to [-180, -90, 180, 90] for layer [{layer_name}].')

    # Create the style and assign it to the created resource
    gs_catalog.save(gs_resource)
    publishing = gs_catalog.get_layer(layer_name) or gs_resource

    sld = None
    if 'sld' in files:
        f = open(files['sld'], 'r')
        sld = f.read()
        f.close()

    style = None
    if sld:
        try:
            style = gs_catalog.get_style(layer_name, workspace=workspace)
        except FailedRequestError:
            style = gs_catalog.get_style(layer_name)

        try:
            overwrite = style or False
            gs_catalog.create_style(layer_name, sld, overwrite=overwrite,
                             raw=True, workspace=workspace)
            gs_catalog.reset()
        except ConflictingDataError as e:
            msg = ('There was already a style named %s in GeoServer, '
                   'try to use: "%s"' % (layer_name + "_layer", str(e)))
            e.args = (msg,)
            raise e
        except UploadError as e:
            msg = ('Error while trying to upload style named %s in GeoServer, '
                   'try to use: "%s"' % (layer_name + "_layer", str(e)))
            e.args = (msg,)
            raise e

        if style is None:
            try:
                style = gs_catalog.get_style(
                    layer_name, workspace=workspace) or gs_catalog.get_style(layer_name)
            except Exception:
                try:
                    style = gs_catalog.get_style(layer_name + '_layer', workspace=workspace) or \
                        gs_catalog.get_style(layer_name + '_layer')
                    overwrite = style or False
                    gs_catalog.create_style(layer_name + '_layer', sld, overwrite=overwrite, raw=True,
                                     workspace=workspace)
                    gs_catalog.reset()
                    style = gs_catalog.get_style(layer_name + '_layer', workspace=workspace) or \
                        gs_catalog.get_style(layer_name + '_layer')
                except ConflictingDataError as e:
                    msg = ('There was already a style named %s in GeoServer, '
                           'cannot overwrite: "%s"' % (layer_name, str(e)))
                    e.args = (msg,)
                    raise e

                style = gs_catalog.get_style(layer_name + "_layer", workspace=workspace) or \
                    gs_catalog.get_style(layer_name + "_layer")
                if style is None:
                    style = gs_catalog.get_style('point')
                    msg = ('Could not find any suitable style in GeoServer '
                           'for Layer: "%s"' % (layer_name))
                    print(msg)

        if style:
            publishing.default_style = style
            print(f'default style set to {layer_name}')
            try:
                gs_catalog.save(publishing)
            except FailedRequestError as e:
                msg = ('Error while trying to save resource named %s in GeoServer, '
                       'try to use: "%s"' % (publishing, str(e)))
                e.args = (msg,)
                raise e

    # Create the Django record for the layer
    alternate = workspace.name + ':' + gs_resource.name
    return dict(
        name=layer_name,
        workspace=workspace.name,
        store=gs_resource.store.name,
        storeType=gs_resource.store.resource_type,
        alternate=alternate,
        title=gs_resource.title or '',
        abstract=gs_resource.abstract or '')
