#!/usr/bin/env

"""

split, clean, and self-cal continuum and line data
  
NOTE: this is intended to be an interactive, iterative process
      so this is more a log that should be run by cutting and
      pasting into casa rather than as an executable script

      search "CHANGEME" for variables to be changed
      
10/9/15 MCA

"""



# ======================== Setup ===========================


# III_57    M0.5      II
# 16:08:39.760 -39:06:25.301

field = 8                                     # CHANGEME 

file_ms = '../science_calibrated.ms'
contspw   = '2,3,4,7,8,9'                      # continuum spectral windows
contspw_w = [128,3840,1920,128,3840,1920]      # continuum spw widths

robust     = 0.5                               # CHANGEME
imsize     = [640,640]
cell       = '0.03arcsec'
imagermode = 'csclean'
refant     = 'DA52'                            # CHANGEME

xc         = 326                               # CHANGEME
yc         = 306                               # CHANGEME
in_a       = 80
out_a      = 120
aper       = 0.5

boxwidth = 300.
box = rg.box([xc-boxwidth,yc-boxwidth],[xc+boxwidth,yc+boxwidth])



# ======================= Split Off Continuum ========================


# split off field from full ms
split(vis = file_ms,
      outputvis = 'f'+str(field)+'.vis',
      field = field,
      datacolumn = 'data')

# split off continuum (take the large bw spw and average
split(vis = 'f'+str(field)+'.vis',
      outputvis = 'f'+str(field)+'_cont.vis',
      spw = contspw,
      width = contspw_w,
      datacolumn = 'data')

# plot uv-distance vs. amplitude
plotms(vis='f'+str(field)+'_cont.vis',
       xaxis='uvdist',yaxis='amp',
       coloraxis='spw')
       # plotfile='f'+str(field)+'_ampuv_orig.png'
       # showgui=False,
       # highres=True,
       # overwrite=True)
# source is unresolved

# find antenna close to center of configuration
# check pipeline log that this ant is OK
plotants(vis='f'+str(field)+'_cont.vis') #, figfile='f'+str(field)+'_ants.png')



                        
# ================== Clean continuum before selfcal ==================


# light clean (100 iterations) to set the mask around the main peaks
# os.system('rm -rf f'+str(field)+'_cont_b4sc*')
clean(vis = 'f'+str(field)+'_cont.vis',
      imagename = 'f'+str(field)+'_cont_b4sc',
      mode = 'mfs',
      psfmode = 'clark',
      niter = 100,
      threshold = '0.0mJy',
      interactive = True,
      mask = '',
      cell = cell,
      imsize = imsize,
      weighting = 'briggs',
      robust = robust,
      imagermode = imagermode)

im_max = imstat(imagename = 'f'+str(field)+'_cont_b4sc.image')['max'][0]
im_rms = imstat(imagename = 'f'+str(field)+'_cont_b4sc.image',
                region='annulus[['+str(xc)+'pix,'+str(yc)+'pix],['+str(in_a)+'pix,'+str(out_a)+'pix]]')['rms'][0]
print 'Peak = {0:.2f} mJy, rms = {1:.2f} mJy, S/N = {2:.1f}'.format(1000*im_max, 1000*im_rms, im_max/im_rms)
# Peak = 1.97 mJy, rms = 0.26 mJy, S/N = 7.7




# ======================== Self-Calibrate 1 ==================

# first combine all the data by time (solint = inf)
# i.e., phase self-cal over entire integration time
gaincal(vis = 'f'+str(field)+'_cont.vis',
        caltable = 'f'+str(field)+'_cont_pcal1',
        refant = refant,
        solint = 'inf',
        combine = 'spw',
        gaintype = 'T',
        spw = '',
        calmode = 'p',
        minblperant = 4,
        minsnr = 3)

# 25 of 32 solutions flagged due to SNR < 3 in spw=0 at 2015/06/15/01:38:31.4
#24 of 31 solutions flagged due to SNR < 3 in spw=0 at 2015/06/15/03:50:17.6


# too many solutions flagged, skipping self-cal


# ======================== Best Continuum Map ==================

# deep clean, trying different robust weights
# os.system('rm -rf f'+str(field)+'_cont_best*')
clean(vis = 'f'+str(field)+'_cont.vis',
      imagename = 'f'+str(field)+'_cont_best',
      mode = 'mfs',
      psfmode = 'clark',
      niter = 2000,
      threshold   = '0.0mJy',
      interactive = True,
      mask = '',
      cell        = cell,
      imsize      = imsize,
      weighting   = 'briggs',
      robust      = 0.5,                                      # CHANGEME
      imagermode  = imagermode)
# placed mask around inner continuum contour
# stopped after 200 iterations once the inside became green


im_max = imstat(imagename = 'f'+str(field)+'_cont_best.image')['max'][0]
im_rms = imstat(imagename = 'f'+str(field)+'_cont_best.image',
                region='annulus[['+str(xc)+'pix,'+str(yc)+'pix],['+str(in_a)+'pix,'+str(out_a)+'pix]]')['rms'][0]
bmaj = imhead(imagename = 'f'+str(field)+'_cont_best.image', mode="get", hdkey="beammajor")
bmin = imhead(imagename = 'f'+str(field)+'_cont_best.image', mode="get", hdkey="beamminor")
print 'Peak = {0:.2f} mJy, rms = {1:.2f} mJy, S/N = {2:.1f}'.format(1000*im_max, 1000*im_rms, im_max/im_rms)
print 'Beam = {0:.2f} x {1:.2f} arcsec'.format(bmaj.get('value'),bmin.get('value'))

# robust = 0.5
# Peak = 1.97 mJy, rms = 0.26 mJy, S/N = 7.7
# Beam = 0.34 x 0.28 arcsec

# save this to a fits file
exportfits(imagename='f'+str(field)+'_cont_best.image', fitsimage='f'+str(field)+'_cont.fits')


# measure flux
# imview(raster=[{'file':'f'+str(field)+'_cont_best.image'}])
im_rms = imstat(imagename = 'f'+str(field)+'_cont_best.image',
                region='annulus[['+str(xc)+'pix,'+str(yc)+'pix],['+str(in_a)+'pix,'+str(out_a)+'pix]]')['rms'][0]
im_flux = imstat(imagename = 'f'+str(field)+'_cont_best.image',
                 region='circle[['+str(xc)+'pix,'+str(yc)+'pix],'+str(aper)+'arcsec]')['flux'][0]
print 'Flux = {0:.2f} mJy, rms = {1:.2f} mJy, S/N = {2:.1f}'.format(1000*im_flux, 1000*im_rms, im_flux/im_rms)
# Flux = 2.03 mJy, rms = 0.26 mJy, S/N = 7.9


# re-center image on source and use get_flux.py to get COG flux
ia.fromimage(outfile = 'f'+str(field)+'_cont_cropped.image',
             infile  = 'f'+str(field)+'_cont.fits',
             region  = box )
ia.close() 
exportfits(imagename = 'f'+str(field)+'_cont_cropped.image',
           fitsimage = 'f'+str(field)+'_cont_cropped.fits')



# ======================== Measure flux with UVMODELFIT ==================

# calculate offset from phase center in arcsec
pixscale = 0.03             # must match 'cell'                 
dx = pixscale*(320.0-xc)    # offset to east (left)
dy = pixscale*(yc-320.0)    # offset to north (up)



# measure flux as gaussian
uvmodelfit(vis       = 'f'+str(field)+'_cont.vis',
           comptype  = 'G',
           sourcepar = [im_flux,dx,dy,0.5,1,0],
           varypar   = [T,T,T,T,T,T],
           niter     = 10)


'''
           
I = 0.0019487 +/- 0.000277321
x = -0.173482 +/- 0.0158212 arcsec
y = -0.412011 +/- 0.0130799 arcsec
a = 2.45508e-06 +/- 3699.73 arcsec
r = 1 +/- 2.07254e+09
p = 63.6369 +/- 57.2958 deg

# a/e_a < 2 so using point source
'''



# measure flux as point source
uvmodelfit(vis       = 'f'+str(field)+'_cont.vis',
           comptype  = 'P',
           sourcepar = [im_flux,dx,dy],
           varypar   = [T,T,T],
           niter     = 10)
'''

reduced chi2=1.38912
I = 0.00199269 +/- 0.000195499
x = -0.173481 +/- 0.015472 arcsec
y = -0.412012 +/- 0.0127912 arcsec

consistent with than aperture method

'''


  




