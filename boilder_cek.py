import OpenOPC
opc = OpenOPC.client(); opc.connect("Mitsubishi.MXOPC.6")
print(opc.list("Dev01.Dynamic Tags.*"))
