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

password_txt = 6000

###########################################################################
## Class Login
###########################################################################

class Login ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"Login"), pos = wx.DefaultPosition, size = wx.Size( 500,221 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        login_layout = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, _(u"login") ), wx.VERTICAL )

        bSizer6 = wx.BoxSizer( wx.VERTICAL )

        self.user_txt = wx.TextCtrl( login_layout.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.user_txt.SetMaxLength( 255 )
        bSizer6.Add( self.user_txt, 0, wx.ALL|wx.EXPAND, 5 )

        self.password_txt = wx.TextCtrl( login_layout.GetStaticBox(), password_txt, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.password_txt.SetMaxLength( 255 )
        bSizer6.Add( self.password_txt, 0, wx.ALL|wx.EXPAND, 5 )


        login_layout.Add( bSizer6, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        self.login_btn = wx.Button( login_layout.GetStaticBox(), wx.ID_ANY, _(u"Login"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.login_btn, 0, wx.ALL, 5 )

        self.exit_btn = wx.Button( login_layout.GetStaticBox(), wx.ID_ANY, _(u"Exit"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.exit_btn, 0, wx.ALL|wx.EXPAND, 5 )


        login_layout.Add( bSizer4, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


        self.SetSizer( login_layout )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.password_txt.Bind( wx.EVT_TEXT_ENTER, self.login )
        self.login_btn.Bind( wx.EVT_BUTTON, self.login )
        self.exit_btn.Bind( wx.EVT_BUTTON, self.exit )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def login( self, event ):
        event.Skip()


    def exit( self, event ):
        event.Skip()


