param(
  [Parameter(Mandatory = $true)]
  [ValidateRange(1, 2147483647)]
  [int]$ProcessId,
  [ValidateRange(1, 8)]
  [int]$MaxDepth = 4,
  [ValidateRange(20, 400)]
  [int]$MaxNodes = 160
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$script:walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$script:treeItems = $null
$script:treeMaxDepth = $MaxDepth
$script:treeMaxNodes = $MaxNodes

function Clip-Text {
  param([AllowNull()][string]$Value, [int]$Limit = 160)
  if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
  $text = $Value -replace '\s+', ' '
  if ($text.Length -gt $Limit) { return $text.Substring(0, $Limit) + '…' }
  return $text
}

function Add-UiaNode {
  param([System.Windows.Automation.AutomationElement]$Element, [int]$Depth)
  if ($script:treeItems.Count -ge $script:treeMaxNodes) { return }
  try { $current = $Element.Current } catch { return }

  $rect = $null
  try {
    $bounds = $current.BoundingRectangle
    if (-not $bounds.IsEmpty) {
      $rect = [pscustomobject]@{
        x = [math]::Round($bounds.X)
        y = [math]::Round($bounds.Y)
        width = [math]::Round($bounds.Width)
        height = [math]::Round($bounds.Height)
      }
    }
  } catch {}

  $invoke = $null
  $value = $null
  $toggle = $null
  $selection = $null
  try { $supportsInvoke = $Element.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$invoke) } catch { $supportsInvoke = $false }
  try { $supportsValue = $Element.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$value) } catch { $supportsValue = $false }
  try { $supportsToggle = $Element.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern, [ref]$toggle) } catch { $supportsToggle = $false }
  try { $supportsSelection = $Element.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern, [ref]$selection) } catch { $supportsSelection = $false }

  $script:treeItems.Add([pscustomobject]@{
    depth = $Depth
    type = $current.ControlType.ProgrammaticName
    name = Clip-Text $current.Name
    automationId = Clip-Text $current.AutomationId 100
    className = Clip-Text $current.ClassName 100
    enabled = $current.IsEnabled
    offscreen = $current.IsOffscreen
    rect = $rect
    patterns = [pscustomobject]@{
      invoke = [bool]$supportsInvoke
      value = [bool]$supportsValue
      toggle = [bool]$supportsToggle
      selectionItem = [bool]$supportsSelection
    }
  }) | Out-Null

  if ($Depth -ge $script:treeMaxDepth) { return }
  try { $child = $script:walker.GetFirstChild($Element) } catch { return }
  while ($null -ne $child -and $script:treeItems.Count -lt $script:treeMaxNodes) {
    try { $next = $script:walker.GetNextSibling($child) } catch { $next = $null }
    Add-UiaNode -Element $child -Depth ($Depth + 1)
    $child = $next
  }
}

$root = [System.Windows.Automation.AutomationElement]::RootElement
$condition = [System.Windows.Automation.Condition]::TrueCondition
$topWindows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
$results = New-Object 'System.Collections.Generic.List[object]'

foreach ($window in $topWindows) {
  try { $info = $window.Current } catch { continue }
  if ($info.ProcessId -ne $ProcessId) { continue }

  $script:treeItems = New-Object 'System.Collections.Generic.List[object]'
  Add-UiaNode -Element $window -Depth 0
  $results.Add([pscustomobject]@{
    title = Clip-Text $info.Name 120
    processId = $info.ProcessId
    nodes = @($script:treeItems.ToArray())
    truncated = ($script:treeItems.Count -ge $MaxNodes)
  }) | Out-Null
}

[pscustomobject]@{
  processId = $ProcessId
  matchedWindows = $results.Count
  windows = @($results.ToArray())
} | ConvertTo-Json -Depth 8 -Compress
