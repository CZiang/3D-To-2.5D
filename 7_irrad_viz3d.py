import matplotlib.pyplot as plt, pyvista

from datetime import datetime, timedelta
from geopandas import GeoDataFrame
from numpy.random import randint
from shapely.geometry import LineString
from t4gpd.commons.GeomLib import GeomLib
from t4gpd.demos.GeoDataFrameDemos import GeoDataFrameDemos
from t4gpd.energy.geoProcesses.DirectSolarIrradiation import DirectSolarIrradiation
from t4gpd.morph.geoProcesses.FootprintExtruder import FootprintExtruder
from t4gpd.morph.geoProcesses.SkyViewFactor import SkyViewFactor
from t4gpd.morph.geoProcesses.STGeoProcess import STGeoProcess
from t4gpd.morph.STPointsDensifier2 import STPointsDensifier2
from t4gpd.pyvista.ToUnstructuredGrid import ToUnstructuredGrid

#~ ======================================================================
def createDatasets():
	buildings = GeoDataFrameDemos.regularGridOfPlots(3, 4, dw=5.0)
	buildings['HAUTEUR'] = 3.0 * randint(2, 7, size=len(buildings))
	buildings.geometry = buildings.geometry.apply(lambda g: GeomLib.normalizeRingOrientation(g)) 

	op = FootprintExtruder(buildings, 'HAUTEUR', forceZCoordToZero=True)
	buildingsIn3d = STGeoProcess(op, buildings).run()

	sensors = STPointsDensifier2(buildings, curvAbsc=[0.25, 0.75], pathidFieldname=None).run()
	sensors['__TMP__'] = list(zip(sensors.geometry, sensors.HAUTEUR))
	sensors.geometry = sensors.__TMP__.apply(lambda t: GeomLib.forceZCoordinateToZ0(t[0], z0=t[1] / 2))
	sensors.geometry = sensors.__TMP__.apply(lambda t: GeomLib.forceZCoordinateToZ0(t[0], z0=randint(1, t[1] - 1)))
	sensors.drop(columns=['__TMP__'], inplace=True)
	return buildings, buildingsIn3d, sensors
	
def plot2D():
	fig, basemap = plt.subplots(figsize=(1.75 * 8.26, 1.2 * 8.26))
	buildings.plot(ax=basemap, color='lightgrey')
	buildings.apply(lambda x: basemap.annotate(
		text=x.HAUTEUR, xy=x.geometry.centroid.coords[0],
		color='red', size=9, ha='center'), axis=1)
	sensors.plot(ax=basemap, column='direct_irradiation', legend=True)
	sensors.apply(lambda x: basemap.annotate(
		# text=x.node_id, xy=x.geometry.coords[0][0:2],
		# text=x.normal_vec, xy=x.geometry.coords[0][0:2],
		text=f'{x.direct_irradiation:.1f}', xy=x.geometry.coords[0][0:2],
		color='black', size=9, ha='center'), axis=1)
	plt.show()
	plt.close(fig)

def plot3D():
	pyvista.global_theme.enable_camera_orientation_widget = True

	scene1 = ToUnstructuredGrid([buildingsIn3d, sensors], 'direct_irradiation').run()
	scene1.plot(scalars='direct_irradiation', cmap='gist_earth', show_edges=False,
		show_scalar_bar=True, point_size=20.0, render_points_as_spheres=True,
		cpos='xy')

#~ ======================================================================
#~ MAIN
buildings, buildingsIn3d, sensors = createDatasets()

# dtStart, dtStop = datetime(2021, 3, 21), datetime(2021, 3, 21)
# dtStart, dtStop = datetime(2021, 6, 21), datetime(2021, 6, 21)
dtStart, dtStop = datetime(2021, 12, 21), datetime(2021, 12, 21)
op = DirectSolarIrradiation(sensors, buildings, 'normal_vec', 'HAUTEUR',
	dtStart, dtStop, dtDelta=timedelta(hours=1))
sensors = STGeoProcess(op, sensors).run()

plot2D()
plot3D()
