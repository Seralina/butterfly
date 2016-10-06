# Butterfly: A Plugin for CFD Analysis (GPL) started by Mostapha Sadeghipour Roudsari
# This file is part of Butterfly.
#
# You should have received a copy of the GNU General Public License
# along with Ladybug; If not, see <http://www.gnu.org/licenses/>.
# 
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>

"""
Load residual values for a case.

-

    Args:
        _recipe: A Butterfly recipe.
        _rect: A rectangle for boundary chart.
        _quants_: Residual quantities. If empty recipe's quantities will be used.
        _targetRes_: Residential number that will be added to the graph as a black line.
            (default: 1e-4).
        timeRange_: timeRange for loading residuals as a domain.
        method_: Method of ploting the values (0..1). 0: Colored mesh, 1: Curves
            If you're updating the values frequently use method 1 which is the
            quicker method.
        _plot: Set to True to plot the chart.
    Returns:
        readMe!: Reports, erros, warnings, etc.
        timeRange: Total time range.
        curves: Lines as curves.
        meshes: Lines as meshes.
        residualLine: Residual line.
        colors: List of colors for meshes to color text, etc.
"""

ghenv.Component.Name = "Butterfly_Plot Residuals"
ghenv.Component.NickName = "plotResiduals"
ghenv.Component.Message = 'VER 0.0.02\nOCT_06_2016'
ghenv.Component.Category = "Butterfly"
ghenv.Component.SubCategory = "07::Etc"
ghenv.Component.AdditionalHelpFromDocStrings = "1"

import Rhino as rc
import scriptcontext as sc
from System.Drawing import Color

def rectFromBoundingBox(bbox):
    p = rc.Geometry.Plane(bbox.Min, rc.Geometry.Vector3d.ZAxis)
    return rc.Geometry.Rectangle3d(p, bbox.Min, bbox.Max)

def rectToRectMapping(geometries, sourceRect, targetRect):
    
    def compoundTransform(geometry, transforms):
        for t in transforms:
            geometry.Transform(t)
        return geometry
    
    # create a plane in the corner or each rect
    sp = rc.Geometry.Plane(sourceRect.Corner(0), sourceRect.Plane.Normal)
    tp = rc.Geometry.Plane(targetRect.Corner(0), targetRect.Plane.Normal)
    
    translate0 = rc.Geometry.Transform.Scale(sp,
                                             targetRect.Width / sourceRect.Width,
                                             targetRect.Height / sourceRect.Height,
                                             1)
    translate1 = rc.Geometry.Transform.PlaneToPlane(sp, tp)
    
    return tuple(compoundTransform(g, (translate0, translate1)) for g in geometries)


def coloredMeshFromCurve(curves, width=10, colors=None):
    def curveToMesh(curve, color):
        oc = curve.Offset(rc.Geometry.Plane.WorldXY, width,
                                      sc.doc.ModelAbsoluteTolerance,
                                      rc.Geometry.CurveOffsetCornerStyle.Sharp)[0]
        
        srf = rc.Geometry.Brep.CreateFromLoft((curve, oc), rc.Geometry.Point3d.Unset,
            rc.Geometry.Point3d.Unset, rc.Geometry.LoftType.Normal, False)[0]
        
        mesh = rc.Geometry.Mesh.CreateFromBrep(srf, rc.Geometry.MeshingParameters.Coarse)[0]
        mesh.VertexColors.CreateMonotoneMesh(color)
        return mesh
        
    meshes = tuple(curveToMesh(curve, color) for curve, color in zip(curves, colors))
    
    return meshes

try:
    import butterfly
    reload(butterfly.parser)
    from butterfly.parser import ResidualParser
except ImportError as e:
    msg = '\nFailed to import butterfly. Did you install butterfly on your machine?' + \
            '\nYou can download the installer file from github: ' + \
            'https://github.com/mostaphaRoudsari/Butterfly/tree/master/plugin/grasshopper/samplefiles' + \
            '\nOpen an issue on github if you think this is a bug:' + \
            ' https://github.com/mostaphaRoudsari/Butterfly/issues'
        
    raise ImportError('{}\n{}'.format(msg, e))

def main():
    try:
        p = ResidualParser(_recipe.logFile)
    except AttributeError:
        p = ResidualParser(_recipe.residualFile)
        
    if not _quants_:
        try:
            quants = p.quantities
        except:
            return
            
    if not quants:
        print 'No residual is loaded! try loading again.'
        return
        
    for q in quants:
        print q
    
    timeRange = '{} To {}'.format(*p.timeRange)
    
    # calculate curves
    crvs = tuple(rc.Geometry.PolylineCurve(rc.Geometry.Point3d(c, float(i), 0)
    for c, i in enumerate(p.getResiduals(quantity, timeRange_))) for quantity in quants)
        
    # find bounding box for curves
    bbox = crvs[0].GetBoundingBox(True)
    
    for crv in crvs[1:]:
        bbox = rc.Geometry.BoundingBox.Union(bbox, crv.GetBoundingBox(True))
    
    # create residual line
    startPt = rc.Geometry.Point3d(0, _targetRes_, 0)
    length = bbox.Max[0] - bbox.Min[0]
    resLine = rc.Geometry.Line(startPt, rc.Geometry.Vector3d(length, 0, 0)).ToNurbsCurve()
    bbox = rc.Geometry.BoundingBox.Union(bbox, resLine.GetBoundingBox(True))
    
    # scale curves
    curves = rectToRectMapping(crvs, rectFromBoundingBox(bbox),
                      rectFromBoundingBox(_rect.GetBoundingBox(True)))
    
    resLine = rectToRectMapping((resLine,), rectFromBoundingBox(bbox),
                                       rectFromBoundingBox(_rect.GetBoundingBox(True)))
    
    # create colored meshes
    cs3 = ((102,194,165), (252,141,98), (141,160,203), (231,138,195),
       (166,216,84), (255,217,47), (229,196,148))
    colors = tuple(Color.FromArgb(*rgb) for rgb in cs3)

    if not method_ % 2:
        residualLine = coloredMeshFromCurve(resLine, width=_lineWidth_,
                                            colors=[Color.Black])
        
        meshes = coloredMeshFromCurve(curves,  width=_lineWidth_,
                                              colors= colors)
        
        ghenv.Component.Params.Output[3].Name = 'meshes'
        ghenv.Component.Params.Output[3].NickName = 'meshes'
        ghenv.Component.Params.Input[4].Name = '_lineWidth_'
        ghenv.Component.Params.Input[4].NickName = '_lineWidth_'
        return timeRange, curves, meshes, residualLine, colors[:len(curves)]
    
    ghenv.Component.Params.Output[3].Name = '.'
    ghenv.Component.Params.Output[3].NickName = '.'
    ghenv.Component.Params.Input[4].Name = '.'
    ghenv.Component.Params.Input[4].NickName = '.'
    
    return timeRange, curves, [], resLine, colors[:len(curves)]
    
if _recipe and _rect and _load:
    
    output = main()
    
    if output:
        timeRange, curves, meshes, residualLine, colors = output