#!/usr/bin/env python
from numpy import *
from scipy.fftpack import *
from matplotlib.pyplot import *

from circular_filt import *
import argparse
import os


class Table:
    def __init__(self, args_in=None):
        parser = argparse.ArgumentParser(description='Process motor data for a table')
        parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
        parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
        parser.add_argument('-s,--table-size', dest="table_size", type=int, default=512)
        parser.add_argument('-i,--index-pos',dest="index_pos", default=0)
        parser.add_argument('-c,--cpr',dest="cpr",default=8192)
        parser.add_argument('-n,--gear-ratio',dest="gear_ratio",type=float,default=1.)
        parser.add_argument('-e,--encoder',dest="encoder_table", action="store_true", default=False)
        parser.add_argument('-t,--torque',dest="torque_table", action="store_true", default=False )
        parser.add_argument('-j,--joint',dest="joint_table", action="store_true", default=False)
        self.args = parser.parse_args(args_in)

        self.data = genfromtxt(self.args.infile, delimiter=',', names=True)
        if (self.args.encoder_table):
            self.table = self.parse_encoder_table(nbins=self.args.table_size,index_pos=self.args.index_pos,cpr=self.args.cpr)
        elif (self.args.joint_table):
            self.table = self.parse_joint_table(nbins=self.args.table_size,index_pos=self.args.index_pos,n=self.args.gear_ratio)
        elif (self.args.torque_table):
            self.table = self.parse_torque_table(nbins=self.args.table_size)
        else:
            self.table = self.parse_cogging_table(nbins=self.args.table_size,index_pos=self.args.index_pos,cpr=self.args.cpr)
        self.save()

    def parse_encoder_table(self, nbins=32, index_pos=0, cpr=8192):
        e = self.data["motor_encoder0"]-float(index_pos)
        vpos = self.data["motor_position0"] 
        y = vpos - e*2*pi/cpr
        x = e*2*pi/cpr     
        i = where(abs(vpos) > .9*max(vpos))
        x = delete(x, i) 
        y = delete(y, i)

        return self.create_table(x, y, nbins)

    def parse_cogging_table(self, nbins=32, index_pos=0, cpr=8192):
        e = self.data["motor_encoder0"]-float(index_pos)
        iq = self.data["iq0"] 
        y = iq
        x = e*2*pi/cpr
        xavg = x-mean(x)     
        i = where(abs(xavg) > .9*max(xavg))
        x = delete(x, i) 
        y = delete(y, i)

        return self.create_table(x, y, nbins)

    def parse_joint_table(self, nbins=32, index_pos=0, n=1.):
        e = self.data["joint_position0"]
        m = self.data["motor_position0"] 
        y = m/n - e
        x = e    
        i = where(abs(e) > .9*max(e))
        x = delete(x, i) 
        y = delete(y, i)
        return self.create_table(x, y, nbins)
    
    def parse_torque_table(self, nbins=32):
        e = self.data["joint_position0"]
        t = self.data["torque0"] 
        y = t
        x = e    
        i = where(abs(e) > .95*max(e))
        x = delete(x, i) 
        y = delete(y, i)
        return self.create_table(x, y, nbins, ffilt=.5)


    def create_table(self, x, y, nbins, ffilt = .05):
        yfilt = circular_filt(x, y-mean(y), nbins=nbins, ffilt=ffilt)
        xfilt = linspace(0, 2*pi, nbins+1)[:-1]

        yfiltd = fft_derivative(xfilt,yfilt)

        pchip = pchip_coeff(xfilt, yfilt, yfiltd)
        xcalc = linspace(0,2*pi,1000)
        ycalc = pchip_calc(pchip, xcalc)
        # figure()
        # plot(xfilt,yfiltd)
        
        figure()
        plot(xfilt,yfilt)
        plot(xfilt, pchip[:,0], '*')
        plot(xcalc, ycalc,'.')
        plot(mod(x,2*pi), y-mean(y),'.')
        show()
        return pchip

    def save(self):
        self.args.outfile.write("{")
        savetxt(self.args.outfile, self.table, delimiter=',', newline="},\n{")
        # remove extra {
        self.args.outfile.seek(0, os.SEEK_END)
        size = self.args.outfile.tell()
        self.args.outfile.truncate(size-1)

if __name__ == "__main__":
    t = Table()
