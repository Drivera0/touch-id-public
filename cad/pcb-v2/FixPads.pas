{ ============================================================================
  FixPads.pas   Altium DelphiScript   for pcb-v2.PcbDoc

  SCOPE: edits pad properties only.
    - deletes nothing
    - creates nothing
    - touches no tracks, vias or polygons
  Routing is done afterwards by hand, on purpose, so the script cannot make
  a routing mistake.

  WHAT IT CHANGES

  1) U2 land pattern (the real defect).  The board currently has the four
     signal pads at +/-0.520 / +/-0.520 mm from the part centre with a
     0.55 mm unrotated thermal.  Correct values, from JLCPCB/LCSC's own
     footprint for C46459900 and TI package drawing DQN0004A 4215302/E:

        pad        X (mm)     Y (mm)    XSize   YSize   Rot
        U2-1       91.979     12.125    0.36    0.30      0
        U2-2       91.979     11.475    0.36    0.30      0
        U2-3       92.821     11.475    0.36    0.30      0
        U2-4       92.821     12.125    0.36    0.30      0
        U2-5       92.400     11.800    0.48    0.48     45

     All five also get Solder Mask Expansion = Manual, -0.05 mm.  Copper on
     a 1x1 X2SON sits 0.054 mm apart no matter what; the mask web is what
     actually stops it bridging at reflow, and the present board has none.

  2) U1-5 (GPIO2) and U1-22 (GPIO8) get net +3V3.  Both are strapping pins
     that Espressif Table 4-1 lists as Floating with no internal pull, and
     both currently read "No Net" in Altium.

     NOTE: assigning a net places NO copper.  It only tells the DRC what
     ought to connect.  Two connections will show as unrouted afterwards and
     must be routed.  That is expected, not a failure.

  RUN: File > Open this .pas, then F9.  Or DXP > Run Script > FixPads.
  ============================================================================ }

Var
    Board : IPCB_Board;
    LOG   : TStringList;

Procedure Say(s : TPCBString);
Begin
    LOG.Add(s);
    LOG.SaveToFile('C:\Users\drive\Documents\Obsidian Vaults\Foundation\touchid\cad\pcb-v2\FixPads-result.txt');
End;

Function FindNet(name : TPCBString) : IPCB_Net;
Var It : IPCB_BoardIterator; N : IPCB_Net;
Begin
    Result := Nil;
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eNetObject));
    It.AddFilter_LayerSet(AllLayers);
    N := It.FirstPCBObject;
    While N <> Nil Do
    Begin
        LOG.Add('    net seen: [' + N.Name + ']');
        If N.Name = name Then Begin Result := N; Break; End;
        N := It.NextPCBObject;
    End;
    Board.BoardIterator_Destroy(It);
End;

{ locate a pad by component designator + pad designator }
Function GetPad(comp, padname : TPCBString) : IPCB_Pad;
Var It : IPCB_BoardIterator; P : IPCB_Pad; c : TPCBString;
Begin
    Result := Nil;
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(ePadObject));
    It.AddFilter_LayerSet(AllLayers);
    P := It.FirstPCBObject;
    While P <> Nil Do
    Begin
        c := '';
        If P.Component <> Nil Then c := P.Component.Name.Text;
        If ((c = comp) And (P.Name = padname))
           Or (P.Name = comp + '-' + padname) Then
        Begin Result := P; Break; End;
        P := It.NextPCBObject;
    End;
    Board.BoardIterator_Destroy(It);
End;

{ logged wrapper }
Function SetPad(comp, padname : TPCBString;
                x, y, xs, ys, rot : Double; mask : Boolean) : Boolean;
Var P : IPCB_Pad;
Begin
    Result := False;
    P := GetPad(comp, padname);
    If P = Nil Then Begin Say('  SetPad ' + comp + '-' + padname + ': PAD NOT FOUND'); Exit; End;
    Say('  SetPad ' + comp + '-' + padname + ': found, was X=' +
        FloatToStr(CoordToMMs(P.X)) + ' Y=' + FloatToStr(CoordToMMs(P.Y)) +
        ' XS=' + FloatToStr(CoordToMMs(P.TopXSize)) +
        ' YS=' + FloatToStr(CoordToMMs(P.TopYSize)) +
        ' rot=' + FloatToStr(P.Rotation));
    PCBServer.SendMessageToRobots(P.I_ObjectAddress, c_Broadcast,
                                  PCBM_BeginModify, c_NoEventData);
    P.X        := MMsToCoord(x);
    P.Y        := MMsToCoord(y);
    P.TopXSize := MMsToCoord(xs);
    P.TopYSize := MMsToCoord(ys);
    P.TopShape := eRectangular;
    P.Rotation := rot;
    If mask Then
    Begin
        P.SolderMaskExpansionMode := eMaskExpansion_Manual;
        P.SolderMaskExpansion     := MMsToCoord(-0.05);
    End;
    PCBServer.SendMessageToRobots(P.I_ObjectAddress, c_Broadcast,
                                  PCBM_EndModify, c_NoEventData);
    Say('           -> now X=' + FloatToStr(CoordToMMs(P.X)) +
        ' Y=' + FloatToStr(CoordToMMs(P.Y)) +
        ' XS=' + FloatToStr(CoordToMMs(P.TopXSize)) +
        ' YS=' + FloatToStr(CoordToMMs(P.TopYSize)) +
        ' rot=' + FloatToStr(P.Rotation));
    Result := True;
End;

Function SetNet(comp, padname, netname : TPCBString) : Boolean;
Var P : IPCB_Pad; N : IPCB_Net;
Begin
    Result := False;
    P := GetPad(comp, padname);
    N := FindNet(netname);
    If P = Nil Then Begin Say('  SetNet ' + comp + '-' + padname + ': PAD NOT FOUND'); Exit; End;
    If N = Nil Then Begin Say('  SetNet ' + comp + '-' + padname + ': NET [' + netname + '] NOT FOUND'); Exit; End;
    PCBServer.SendMessageToRobots(P.I_ObjectAddress, c_Broadcast,
                                  PCBM_BeginModify, c_NoEventData);
    P.Net := N;
    PCBServer.SendMessageToRobots(P.I_ObjectAddress, c_Broadcast,
                                  PCBM_EndModify, c_NoEventData);
    Say('  SetNet ' + comp + '-' + padname + ': assigned [' + netname + ']');
    Result := True;
End;

Procedure FixPads;
Var ok, bad : Integer; msg : TPCBString;
Begin
    LOG := TStringList.Create;
    Say('FixPads run started');
    Board := PCBServer.GetCurrentPCBBoard;
    If Board = Nil Then
    Begin
        Say('FATAL: GetCurrentPCBBoard returned Nil. No PCB is current.');
        ShowMessage('Open pcb-v2.PcbDoc first.');
        Exit;
    End;
    Say('board acquired: ' + Board.FileName);

    ok := 0; bad := 0; msg := '';
    PCBServer.PreProcess;

    If SetPad('U2','1', 91.9790, 12.1250, 0.36, 0.30,  0, True) Then Inc(ok)
       Else Begin Inc(bad); msg := msg + 'U2-1 not found' + #13#10; End;
    If SetPad('U2','2', 91.9790, 11.4750, 0.36, 0.30,  0, True) Then Inc(ok)
       Else Begin Inc(bad); msg := msg + 'U2-2 not found' + #13#10; End;
    If SetPad('U2','3', 92.8210, 11.4750, 0.36, 0.30,  0, True) Then Inc(ok)
       Else Begin Inc(bad); msg := msg + 'U2-3 not found' + #13#10; End;
    If SetPad('U2','4', 92.8210, 12.1250, 0.36, 0.30,  0, True) Then Inc(ok)
       Else Begin Inc(bad); msg := msg + 'U2-4 not found' + #13#10; End;
    If SetPad('U2','5', 92.4000, 11.8000, 0.48, 0.48, 45, True) Then Inc(ok)
       Else Begin Inc(bad); msg := msg + 'U2-5 not found' + #13#10; End;

    If SetNet('U1','5',  '+3V3') Then Inc(ok)
       Else Begin Inc(bad); msg := msg + 'U1-5 net not set' + #13#10; End;
    If SetNet('U1','22', '+3V3') Then Inc(ok)
       Else Begin Inc(bad); msg := msg + 'U1-22 net not set' + #13#10; End;

    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    Client.SendMessage('PCB:Zoom', 'Action=Redraw', 255, Client.CurrentView);

    Say('RESULT: ' + IntToStr(ok) + ' of 7 applied, ' + IntToStr(bad) + ' failed.');
    Say('--- end ---');
    ShowMessage('FixPads: ' + IntToStr(ok) + ' of 7 edits applied, ' +
                IntToStr(bad) + ' failed.' + #13#10 + msg + #13#10 +
                'U1-5 and U1-22 now have a net but NO copper. ' +
                'Two connections will show as unrouted. Route them next.');
End;
