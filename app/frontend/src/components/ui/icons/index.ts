'use client';

/**
 * Icon Abstraction Layer
 * 
 * Re-exports icons using the uniform createIcon wrapper.
 * Now backed by lucide-react.
 */

import { createIcon } from './Icon';
import {
    Plus,
    PlusCircle,
    Check,
    X,
    Copy,
    Trash2,
    Pencil,
    RefreshCw,
    Search,
    Share2,
    Send,
    Square,
    ArrowRight,
    ArrowUp,
    ChevronLeft,
    ChevronRight,
    ChevronUp,
    ChevronDown,
    Menu,
    Home,
    Inbox,
    CloudUpload,
    FolderPlus,
    FileText,
    FolderOpen,
    FileUp,
    LayoutDashboard,
    Minimize2,
    Download,
    Circle,
    Maximize,
    Minimize,
    Bell,
    CheckCircle,
    Grid,
    LayoutGrid,
    HelpCircle,
    History,
    Image,
    Layers,
    List,
    Link,
    Mic,
    MoreVertical,
    MoreHorizontal,
    Move,
    Users,
    Brain,
    Settings,
    StickyNote,
    Tag,
    TrendingUp,
    Sliders,
    Cloud,
    Lock,
    ExternalLink,
    GripHorizontal,
    PanelLeftClose,
    PanelLeftOpen,
    PanelRightClose,
    PanelRightOpen,
    CreditCard,
    DollarSign,
    Zap,
    MapPin,
    ParkingSquare,
    TriangleAlert,
    CircleAlert,
    Info,
    Bot,
    MessageSquare,
    Sparkles,
    ZoomIn,
    ZoomOut,
    Workflow,
    Target,
    User,
    Palette,
    LogOut,
    Eye,
    EyeOff,
    Key,
    Database,
    MousePointer2,
    Hand,
    Scan
} from 'lucide-react';

// Action icons
export const AddIcon = createIcon(Plus, 'AddIcon');
export const AddCircleIcon = createIcon(PlusCircle, 'AddCircleIcon');
export const CheckIcon = createIcon(Check, 'CheckIcon');
export const CloseIcon = createIcon(X, 'CloseIcon');
export const ContentCopyIcon = createIcon(Copy, 'ContentCopyIcon');
export const DeleteIcon = createIcon(Trash2, 'DeleteIcon');
export const EditIcon = createIcon(Pencil, 'EditIcon');
export const RefreshIcon = createIcon(RefreshCw, 'RefreshIcon');
export const SearchIcon = createIcon(Search, 'SearchIcon');
export const ShareIcon = createIcon(Share2, 'ShareIcon');
export const SendIcon = createIcon(Send, 'SendIcon');
export const StopIcon = createIcon(Square, 'StopIcon');
export const VisibilityIcon = createIcon(Eye, 'VisibilityIcon');
export const VisibilityOffIcon = createIcon(EyeOff, 'VisibilityOffIcon');

// Navigation icons
export const ArrowForwardIcon = createIcon(ArrowRight, 'ArrowForwardIcon');
export const ArrowUpwardIcon = createIcon(ArrowUp, 'ArrowUpwardIcon');
export const ChevronLeftIcon = createIcon(ChevronLeft, 'ChevronLeftIcon');
export const ChevronRightIcon = createIcon(ChevronRight, 'ChevronRightIcon');
export const ExpandLessIcon = createIcon(ChevronUp, 'ExpandLessIcon');
export const ExpandMoreIcon = createIcon(ChevronDown, 'ExpandMoreIcon');
export const MenuOpenIcon = createIcon(Menu, 'MenuOpenIcon');
export const HomeIcon = createIcon(Home, 'HomeIcon');
export const InboxIcon = createIcon(Inbox, 'InboxIcon');
export const KeyboardArrowDownIcon = createIcon(ChevronDown, 'KeyboardArrowDownIcon');
export const LogoutIcon = createIcon(LogOut, 'LogoutIcon');

// File/Folder icons
export const CloudUploadIcon = createIcon(CloudUpload, 'CloudUploadIcon');
export const CreateNewFolderIcon = createIcon(FolderPlus, 'CreateNewFolderIcon');
export const DescriptionIcon = createIcon(FileText, 'DescriptionIcon');
export const FolderOpenIcon = createIcon(FolderOpen, 'FolderOpenIcon');
export const UploadFileIcon = createIcon(FileUp, 'UploadFileIcon');

// Layout/View icons
export const DashboardIcon = createIcon(LayoutDashboard, 'DashboardIcon');
export const DockIcon = createIcon(Minimize2, 'DockIcon');
export const DownloadIcon = createIcon(Download, 'DownloadIcon');
export const CircleIcon = createIcon(Circle, 'CircleIcon');
export const FullscreenIcon = createIcon(Maximize, 'FullscreenIcon');
export const FullscreenExitIcon = createIcon(Minimize, 'FullscreenExitIcon');
export const NotificationsIcon = createIcon(Bell, 'NotificationsIcon');
export const CheckCircleIcon = createIcon(CheckCircle, 'CheckCircleIcon');
export const Grid4x4Icon = createIcon(Grid, 'Grid4x4Icon');
export const GridViewIcon = createIcon(LayoutGrid, 'GridViewIcon');
export const LayersIcon = createIcon(Layers, 'LayersIcon');
export const ViewListIcon = createIcon(List, 'ViewListIcon');
export const ZoomInIcon = createIcon(ZoomIn, 'ZoomInIcon');
export const ZoomOutIcon = createIcon(ZoomOut, 'ZoomOutIcon');
export const PaletteIcon = createIcon(Palette, 'PaletteIcon');

// Status/Alert icons
export const ErrorIcon = createIcon(CircleAlert, 'ErrorIcon');
export const HelpOutlineIcon = createIcon(HelpCircle, 'HelpOutlineIcon');
export const InfoIcon = createIcon(Info, 'InfoIcon');
export const WarningIcon = createIcon(TriangleAlert, 'WarningIcon');

// AI/Brain icons
export const AutoAwesomeIcon = createIcon(Sparkles, 'AutoAwesomeIcon');
export const BoltIcon = createIcon(Zap, 'BoltIcon');
export const PsychologyIcon = createIcon(Brain, 'PsychologyIcon');
export const BotIcon = createIcon(Bot, 'BotIcon');
export const BrainIcon = createIcon(Brain, 'BrainIcon');
export const ChatIcon = createIcon(MessageSquare, 'ChatIcon');
export const MessageSquareIcon = createIcon(MessageSquare, 'MessageSquareIcon');
export const StorageIcon = createIcon(Database, 'StorageIcon');

// Misc icons
export const AccountTreeIcon = createIcon(Workflow, 'AccountTreeIcon');
export const AttachMoneyIcon = createIcon(DollarSign, 'AttachMoneyIcon');
export const CreditCardIcon = createIcon(CreditCard, 'CreditCardIcon');
export const DragIndicatorIcon = createIcon(GripHorizontal, 'DragIndicatorIcon');
export const GpsFixedIcon = createIcon(Target, 'GpsFixedIcon');
export const HistoryIcon = createIcon(History, 'HistoryIcon');
export const ImageSearchIcon = createIcon(Image, 'ImageSearchIcon');
export const LinkIcon = createIcon(Link, 'LinkIcon');
export const LocalParkingIcon = createIcon(ParkingSquare, 'LocalParkingIcon');
export const MicIcon = createIcon(Mic, 'MicIcon');
export const MoreVertIcon = createIcon(MoreVertical, 'MoreVertIcon');
export const MoreHorizIcon = createIcon(MoreHorizontal, 'MoreHorizIcon');
export const OpenWithIcon = createIcon(Move, 'OpenWithIcon');
export const PeopleIcon = createIcon(Users, 'PeopleIcon');
export const PersonIcon = createIcon(User, 'PersonIcon');
export const SettingsIcon = createIcon(Settings, 'SettingsIcon');
export const StickyNote2Icon = createIcon(StickyNote, 'StickyNote2Icon');
export const TagIcon = createIcon(Tag, 'TagIcon');
export const TrendingUpIcon = createIcon(TrendingUp, 'TrendingUpIcon');
export const TuneIcon = createIcon(Sliders, 'TuneIcon');
export const CloudIcon = createIcon(Cloud, 'CloudIcon');
export const LockIcon = createIcon(Lock, 'LockIcon');
export const KeyIcon = createIcon(Key, 'KeyIcon');
export const ExternalLinkIcon = createIcon(ExternalLink, 'ExternalLinkIcon');
export const GripHorizontalIcon = createIcon(GripHorizontal, 'GripHorizontalIcon');
export const PanelRightCloseIcon = createIcon(PanelRightClose, 'PanelRightCloseIcon');
export const PanelRightOpenIcon = createIcon(PanelRightOpen, 'PanelRightOpenIcon');

// Tool icons
export const MousePointerIcon = createIcon(MousePointer2, 'MousePointerIcon');
export const HandIcon = createIcon(Hand, 'HandIcon');
export const ScanIcon = createIcon(Scan, 'ScanIcon');

// Re-export types
export type { IconProps, IconSize, IconColor } from './types';
export { sizeMap } from './types';
