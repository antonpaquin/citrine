#! /bin/bash

vboxmanage modifyvm "hivemind_build_macos" --cpuidset 00000001 000106e5 00100800 0098e3fd bfebfbff
vboxmanage setextradata "hivemind_build_macos" "VBoxInternal/Devices/efi/0/Config/DmiSystemProduct" "iMac11,3"
vboxmanage setextradata "hivemind_build_macos" "VBoxInternal/Devices/efi/0/Config/DmiSystemVersion" "1.0"
vboxmanage setextradata "hivemind_build_macos" "VBoxInternal/Devices/efi/0/Config/DmiBoardProduct" "Iloveapple"
vboxmanage setextradata "hivemind_build_macos" "VBoxInternal/Devices/smc/0/Config/DeviceKey" "ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc"
vboxmanage setextradata "hivemind_build_macos" "VBoxInternal/Devices/smc/0/Config/GetKeyFromRealSMC" 1

