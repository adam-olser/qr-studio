import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Palette,
  Eye,
  Settings,
  Sparkles,
  Zap,
  Layers,
  Square,
  Circle,
  Minus,
  HelpCircle,
} from "lucide-react";
import { QRConfig } from "@/types/qr";

interface StyleControlsProps {
  config: QRConfig;
  onConfigChange: (updates: Partial<QRConfig>) => void;
  disabled?: boolean;
}

const STYLE_OPTIONS = [
  { value: "square", label: "Square", icon: Square },
  { value: "gapped", label: "Gapped", icon: Minus },
  { value: "dots", label: "Dots", icon: Circle },
  { value: "rounded", label: "Rounded", icon: Circle },
  { value: "bars-vertical", label: "Vertical Bars", icon: Layers },
  { value: "bars-horizontal", label: "Horizontal Bars", icon: Layers },
];

const EYE_SHAPE_OPTIONS = [
  { value: "rect", label: "Rectangle" },
  { value: "rounded", label: "Rounded" },
  { value: "circle", label: "Circle" },
];

const EYE_STYLE_OPTIONS = [
  { value: "standard", label: "Standard" },
  { value: "circle-ring", label: "Circle Ring" },
];

const ERROR_CORRECTION_OPTIONS = [
  { value: "L", label: "Low (7%)", description: "Best for simple designs" },
  { value: "M", label: "Medium (15%)", description: "Good balance" },
  { value: "Q", label: "Quartile (25%)", description: "Recommended" },
  { value: "H", label: "High (30%)", description: "Best for logos" },
];

export function StyleControls({
  config,
  onConfigChange,
  disabled = false,
}: StyleControlsProps) {
  const handleColorChange = (type: "dark" | "light", color: string) => {
    if (type === "dark") {
      onConfigChange({ dark_color: color });
    } else {
      onConfigChange({ light_color: color });
    }
  };

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Module Style */}
        <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-600" />
              Module Style
            </CardTitle>
            <CardDescription>
              Choose how the QR code modules (dots) are drawn
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {STYLE_OPTIONS.map((style) => {
                const Icon = style.icon;
                return (
                  <Button
                    key={style.value}
                    variant={
                      config.style === style.value ? "default" : "outline"
                    }
                    size="sm"
                    onClick={() =>
                      onConfigChange({
                        style: style.value as QRConfig["style"],
                      })
                    }
                    disabled={disabled}
                    className={`h-auto p-3 flex flex-col items-center gap-2 transition-all duration-200 ${
                      config.style === style.value
                        ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg"
                        : "hover:bg-purple-50 hover:border-purple-300"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="text-xs font-medium">{style.label}</span>
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Colors */}
        <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Palette className="h-5 w-5 text-blue-600" />
              Colors
            </CardTitle>
            <CardDescription>
              Customize the foreground and background colors
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="dark-color" className="text-sm font-medium">
                  Foreground Color
                </Label>
                <div className="flex gap-2">
                  <Input
                    id="dark-color"
                    type="color"
                    value={config.dark_color}
                    onChange={(e) => handleColorChange("dark", e.target.value)}
                    disabled={disabled}
                    className="w-16 h-10 p-1 border-2 border-gray-200 rounded-lg cursor-pointer"
                  />
                  <Input
                    type="text"
                    value={config.dark_color}
                    onChange={(e) => handleColorChange("dark", e.target.value)}
                    disabled={disabled}
                    placeholder="#000000"
                    className="flex-1"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="light-color" className="text-sm font-medium">
                  Background Color
                </Label>
                <div className="flex gap-2">
                  <Input
                    id="light-color"
                    type="color"
                    value={config.light_color}
                    onChange={(e) => handleColorChange("light", e.target.value)}
                    disabled={disabled}
                    className="w-16 h-10 p-1 border-2 border-gray-200 rounded-lg cursor-pointer"
                  />
                  <Input
                    type="text"
                    value={config.light_color}
                    onChange={(e) => handleColorChange("light", e.target.value)}
                    disabled={disabled}
                    placeholder="#FFFFFF"
                    className="flex-1"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Eye Customization */}
        <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Eye className="h-5 w-5 text-green-600" />
              Eye Customization
            </CardTitle>
            <CardDescription>
              Customize the corner finder patterns (eyes)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="eye-shape" className="text-sm font-medium">
                  Eye Shape
                </Label>
                <Select
                  value={config.eye_shape}
                  onValueChange={(value) =>
                    onConfigChange({
                      eye_shape: value as QRConfig["eye_shape"],
                    })
                  }
                  disabled={disabled}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EYE_SHAPE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="eye-style" className="text-sm font-medium">
                  Eye Style
                </Label>
                <Select
                  value={config.eye_style}
                  onValueChange={(value) =>
                    onConfigChange({
                      eye_style: value as QRConfig["eye_style"],
                    })
                  }
                  disabled={disabled}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EYE_STYLE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Separator />

            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Eye Radius</Label>
                  <span className="text-xs text-gray-500">
                    {config.eye_radius.toFixed(1)}
                  </span>
                </div>
                <Slider
                  value={[config.eye_radius]}
                  onValueChange={([value]) =>
                    onConfigChange({ eye_radius: value })
                  }
                  min={0.1}
                  max={1.0}
                  step={0.1}
                  disabled={disabled}
                  className="w-full"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Scale X</Label>
                    <span className="text-xs text-gray-500">
                      {config.eye_scale_x.toFixed(1)}
                    </span>
                  </div>
                  <Slider
                    value={[config.eye_scale_x]}
                    onValueChange={([value]) =>
                      onConfigChange({ eye_scale_x: value })
                    }
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    disabled={disabled}
                    className="w-full"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Scale Y</Label>
                    <span className="text-xs text-gray-500">
                      {config.eye_scale_y.toFixed(1)}
                    </span>
                  </div>
                  <Slider
                    value={[config.eye_scale_y]}
                    onValueChange={([value]) =>
                      onConfigChange({ eye_scale_y: value })
                    }
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    disabled={disabled}
                    className="w-full"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Error Correction */}
        <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-600" />
              Error Correction
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">
                    Higher levels (Q, H) are better for QR codes with logos as
                    they can recover from more damage or obstruction.
                  </p>
                </TooltipContent>
              </Tooltip>
            </CardTitle>
            <CardDescription>
              Higher levels allow more damage while maintaining readability
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Select
              value={config.ec_level}
              onValueChange={(value) =>
                onConfigChange({ ec_level: value as QRConfig["ec_level"] })
              }
              disabled={disabled}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ERROR_CORRECTION_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex flex-col">
                      <span>{option.label}</span>
                      <span className="text-xs text-gray-500">
                        {option.description}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        {/* Size & Border */}
        <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Settings className="h-5 w-5 text-gray-600" />
              Size & Border
            </CardTitle>
            <CardDescription>
              Adjust the output size and border width
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Output Size</Label>
                <span className="text-xs text-gray-500">
                  {config.size} × {config.size}px
                </span>
              </div>
              <Slider
                value={[config.size]}
                onValueChange={([value]) => onConfigChange({ size: value })}
                min={256}
                max={2048}
                step={64}
                disabled={disabled}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>256px</span>
                <span>1024px</span>
                <span>2048px</span>
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Border Width</Label>
                <span className="text-xs text-gray-500">
                  {config.border} modules
                </span>
              </div>
              <Slider
                value={[config.border]}
                onValueChange={([value]) => onConfigChange({ border: value })}
                min={0}
                max={10}
                step={1}
                disabled={disabled}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0</span>
                <span>5</span>
                <span>10</span>
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">QR Radius</Label>
                <span className="text-xs text-gray-500">
                  {config.qr_radius}px
                </span>
              </div>
              <Slider
                value={[config.qr_radius]}
                onValueChange={([value]) =>
                  onConfigChange({ qr_radius: value })
                }
                min={0}
                max={50}
                step={1}
                disabled={disabled}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0px</span>
                <span>25px</span>
                <span>50px</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Output Optimization */}
        <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-600" />
              Output Optimization
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">
                    Higher compression = smaller files but slower generation.
                    More colors = better quality but larger files.
                  </p>
                </TooltipContent>
              </Tooltip>
            </CardTitle>
            <CardDescription>
              Optimize file size and quality for different use cases
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Compression Level</Label>
                <span className="text-xs text-gray-500">
                  {config.compress_level}/9
                </span>
              </div>
              <Slider
                value={[config.compress_level]}
                onValueChange={([value]) =>
                  onConfigChange({ compress_level: value })
                }
                min={0}
                max={9}
                step={1}
                disabled={disabled}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Fast</span>
                <span>Balanced</span>
                <span>Small</span>
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">
                  Color Quantization
                </Label>
                <span className="text-xs text-gray-500">
                  {config.quantize_colors} colors
                </span>
              </div>
              <Slider
                value={[config.quantize_colors]}
                onValueChange={([value]) =>
                  onConfigChange({ quantize_colors: value })
                }
                min={2}
                max={256}
                step={2}
                disabled={disabled}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>2 colors</span>
                <span>64 colors</span>
                <span>256 colors</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  );
}
