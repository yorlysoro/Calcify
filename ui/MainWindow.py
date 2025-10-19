# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

import gettext
_ = gettext.gettext

###########################################################################
## Class MainWindowFrame
###########################################################################

class MainWindowFrame ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"Menu"), pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        sbSizer2 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, _(u"Menu") ), wx.VERTICAL )

        bSizer14 = wx.BoxSizer( wx.HORIZONTAL )

        self.sales_btn = wx.Button( sbSizer2.GetStaticBox(), wx.ID_ANY, _(u"Sales"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer14.Add( self.sales_btn, 0, wx.ALL, 5 )

        self.purchases_btn = wx.Button( sbSizer2.GetStaticBox(), wx.ID_ANY, _(u"Purchases"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer14.Add( self.purchases_btn, 0, wx.ALL, 5 )


        sbSizer2.Add( bSizer14, 1, wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 5 )

        bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

        self.currencies_btn = wx.Button( sbSizer2.GetStaticBox(), wx.ID_ANY, _(u"Currencies"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer15.Add( self.currencies_btn, 0, wx.ALL, 5 )

        self.products_btn = wx.Button( sbSizer2.GetStaticBox(), wx.ID_ANY, _(u"Products"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer15.Add( self.products_btn, 0, wx.ALL, 5 )


        sbSizer2.Add( bSizer15, 1, wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 5 )

        bSizer16 = wx.BoxSizer( wx.HORIZONTAL )

        self.config_btn = wx.Button( sbSizer2.GetStaticBox(), wx.ID_ANY, _(u"Configuration"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer16.Add( self.config_btn, 0, wx.ALL, 5 )

        self.exit_btn = wx.Button( sbSizer2.GetStaticBox(), wx.ID_ANY, _(u"Exit"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer16.Add( self.exit_btn, 0, wx.ALL, 5 )


        sbSizer2.Add( bSizer16, 1, wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 5 )


        self.SetSizer( sbSizer2 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.sales_btn.Bind( wx.EVT_BUTTON, self.sales )
        self.purchases_btn.Bind( wx.EVT_BUTTON, self.purchases )
        self.currencies_btn.Bind( wx.EVT_BUTTON, self.currencies )
        self.products_btn.Bind( wx.EVT_BUTTON, self.products )
        self.config_btn.Bind( wx.EVT_BUTTON, self.config )
        self.exit_btn.Bind( wx.EVT_BUTTON, self.exit )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def sales( self, event ):
        event.Skip()

    def purchases( self, event ):
        event.Skip()

    def currencies( self, event ):
        event.Skip()

    def products( self, event ):
        event.Skip()

    def config( self, event ):
        event.Skip()

    def exit( self, event ):
        event.Skip()


