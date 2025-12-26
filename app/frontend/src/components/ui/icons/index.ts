'use client';

/**
 * Icon Abstraction Layer
 * 
 * This module provides a centralized icon system that abstracts away the underlying
 * icon library. Currently implemented with @mui/icons-material.
 * 
 * Usage:
 *   import { AddIcon, CloseIcon } from '@/components/ui/icons';
 *   <AddIcon size="md" color="primary" />
 * 
 * To swap icon libraries in the future, only this file needs to be updated.
 */

import { createIcon } from './Icon';

// MUI Icons imports
import AddMui from '@mui/icons-material/Add';
import AddCircleMui from '@mui/icons-material/AddCircle';
import AccountTreeMui from '@mui/icons-material/AccountTree';
import ArrowForwardMui from '@mui/icons-material/ArrowForward';
import ArrowUpwardMui from '@mui/icons-material/ArrowUpward';
import AttachMoneyMui from '@mui/icons-material/AttachMoney';
import AutoAwesomeMui from '@mui/icons-material/AutoAwesome';
import BoltMui from '@mui/icons-material/Bolt';
import CheckMui from '@mui/icons-material/Check';
import ChevronLeftMui from '@mui/icons-material/ChevronLeft';
import ChevronRightMui from '@mui/icons-material/ChevronRight';
import MenuOpenMui from '@mui/icons-material/MenuOpen';
import CloseMui from '@mui/icons-material/Close';
import CloudUploadMui from '@mui/icons-material/CloudUpload';
import ContentCopyMui from '@mui/icons-material/ContentCopy';
import CreateNewFolderMui from '@mui/icons-material/CreateNewFolder';
import CreditCardMui from '@mui/icons-material/CreditCard';
import DashboardMui from '@mui/icons-material/Dashboard';
import DeleteMui from '@mui/icons-material/Delete';
import DescriptionMui from '@mui/icons-material/Description';
import DockMui from '@mui/icons-material/Dock';
import DownloadMui from '@mui/icons-material/Download';
import CircleMui from '@mui/icons-material/Circle';
import DragIndicatorMui from '@mui/icons-material/DragIndicator';
import EditMui from '@mui/icons-material/Edit';
import ErrorMui from '@mui/icons-material/Error';
import ExpandLessMui from '@mui/icons-material/ExpandLess';
import ExpandMoreMui from '@mui/icons-material/ExpandMore';
import FolderOpenMui from '@mui/icons-material/FolderOpen';
import FullscreenMui from '@mui/icons-material/Fullscreen';
import FullscreenExitMui from '@mui/icons-material/FullscreenExit';
import NotificationsMui from '@mui/icons-material/Notifications';
import CheckCircleMui from '@mui/icons-material/CheckCircle';
import GpsFixedMui from '@mui/icons-material/GpsFixed';
import Grid4x4Mui from '@mui/icons-material/Grid4x4';
import GridViewMui from '@mui/icons-material/GridView';
import HelpOutlineMui from '@mui/icons-material/HelpOutline';
import HistoryMui from '@mui/icons-material/History';
import HomeMui from '@mui/icons-material/Home';
import ImageSearchMui from '@mui/icons-material/ImageSearch';
import LayersMui from '@mui/icons-material/Layers';
import LinkMui from '@mui/icons-material/Link';
import LocalParkingMui from '@mui/icons-material/LocalParking';
import MicMui from '@mui/icons-material/Mic';
import MoreVertMui from '@mui/icons-material/MoreVert';
import OpenWithMui from '@mui/icons-material/OpenWith';
import PeopleMui from '@mui/icons-material/People';
import PsychologyMui from '@mui/icons-material/Psychology';
import RefreshMui from '@mui/icons-material/Refresh';
import SearchMui from '@mui/icons-material/Search';
import SettingsMui from '@mui/icons-material/Settings';
import ShareMui from '@mui/icons-material/Share';
import StickyNote2Mui from '@mui/icons-material/StickyNote2';
import TagMui from '@mui/icons-material/Tag';
import TrendingUpMui from '@mui/icons-material/TrendingUp';
import TuneMui from '@mui/icons-material/Tune';
import UploadFileMui from '@mui/icons-material/UploadFile';
import ViewListMui from '@mui/icons-material/ViewList';
import WarningMui from '@mui/icons-material/Warning';
import ZoomInMui from '@mui/icons-material/ZoomIn';
import ZoomOutMui from '@mui/icons-material/ZoomOut';
import SendMui from '@mui/icons-material/Send';
import StopMui from '@mui/icons-material/Stop';
import MoreHorizMui from '@mui/icons-material/MoreHoriz';
import InfoMui from '@mui/icons-material/Info';
import KeyboardArrowDownMui from '@mui/icons-material/KeyboardArrowDown';

// Create wrapped icons with consistent API
// Naming convention: [Name]Icon

// Action icons
export const AddIcon = createIcon(AddMui, 'AddIcon');
export const AddCircleIcon = createIcon(AddCircleMui, 'AddCircleIcon');
export const CheckIcon = createIcon(CheckMui, 'CheckIcon');
export const CloseIcon = createIcon(CloseMui, 'CloseIcon');
export const ContentCopyIcon = createIcon(ContentCopyMui, 'ContentCopyIcon');
export const DeleteIcon = createIcon(DeleteMui, 'DeleteIcon');
export const EditIcon = createIcon(EditMui, 'EditIcon');
export const RefreshIcon = createIcon(RefreshMui, 'RefreshIcon');
export const SearchIcon = createIcon(SearchMui, 'SearchIcon');
export const ShareIcon = createIcon(ShareMui, 'ShareIcon');
export const SendIcon = createIcon(SendMui, 'SendIcon');
export const StopIcon = createIcon(StopMui, 'StopIcon');

// Navigation icons
export const ArrowForwardIcon = createIcon(ArrowForwardMui, 'ArrowForwardIcon');
export const ArrowUpwardIcon = createIcon(ArrowUpwardMui, 'ArrowUpwardIcon');
export const ChevronLeftIcon = createIcon(ChevronLeftMui, 'ChevronLeftIcon');
export const ChevronRightIcon = createIcon(ChevronRightMui, 'ChevronRightIcon');
export const ExpandLessIcon = createIcon(ExpandLessMui, 'ExpandLessIcon');
export const ExpandMoreIcon = createIcon(ExpandMoreMui, 'ExpandMoreIcon');
export const MenuOpenIcon = createIcon(MenuOpenMui, 'MenuOpenIcon');
export const HomeIcon = createIcon(HomeMui, 'HomeIcon');
export const KeyboardArrowDownIcon = createIcon(KeyboardArrowDownMui, 'KeyboardArrowDownIcon');

// File/Folder icons
export const CloudUploadIcon = createIcon(CloudUploadMui, 'CloudUploadIcon');
export const CreateNewFolderIcon = createIcon(CreateNewFolderMui, 'CreateNewFolderIcon');
export const DescriptionIcon = createIcon(DescriptionMui, 'DescriptionIcon');
export const FolderOpenIcon = createIcon(FolderOpenMui, 'FolderOpenIcon');
export const UploadFileIcon = createIcon(UploadFileMui, 'UploadFileIcon');

// Layout/View icons
export const DashboardIcon = createIcon(DashboardMui, 'DashboardIcon');
export const DockIcon = createIcon(DockMui, 'DockIcon');
export const DownloadIcon = createIcon(DownloadMui, 'DownloadIcon');
export const CircleIcon = createIcon(CircleMui, 'CircleIcon');
export const FullscreenIcon = createIcon(FullscreenMui, 'FullscreenIcon');
export const FullscreenExitIcon = createIcon(FullscreenExitMui, 'FullscreenExitIcon');
export const NotificationsIcon = createIcon(NotificationsMui, 'NotificationsIcon');
export const CheckCircleIcon = createIcon(CheckCircleMui, 'CheckCircleIcon');
export const Grid4x4Icon = createIcon(Grid4x4Mui, 'Grid4x4Icon');
export const GridViewIcon = createIcon(GridViewMui, 'GridViewIcon');
export const LayersIcon = createIcon(LayersMui, 'LayersIcon');
export const ViewListIcon = createIcon(ViewListMui, 'ViewListIcon');
export const ZoomInIcon = createIcon(ZoomInMui, 'ZoomInIcon');
export const ZoomOutIcon = createIcon(ZoomOutMui, 'ZoomOutIcon');

// Status/Alert icons
export const ErrorIcon = createIcon(ErrorMui, 'ErrorIcon');
export const HelpOutlineIcon = createIcon(HelpOutlineMui, 'HelpOutlineIcon');
export const InfoIcon = createIcon(InfoMui, 'InfoIcon');
export const WarningIcon = createIcon(WarningMui, 'WarningIcon');

// AI/Brain icons
export const AutoAwesomeIcon = createIcon(AutoAwesomeMui, 'AutoAwesomeIcon');
export const BoltIcon = createIcon(BoltMui, 'BoltIcon');
export const PsychologyIcon = createIcon(PsychologyMui, 'PsychologyIcon');

// Misc icons
export const AccountTreeIcon = createIcon(AccountTreeMui, 'AccountTreeIcon');
export const AttachMoneyIcon = createIcon(AttachMoneyMui, 'AttachMoneyIcon');
export const CreditCardIcon = createIcon(CreditCardMui, 'CreditCardIcon');
export const DragIndicatorIcon = createIcon(DragIndicatorMui, 'DragIndicatorIcon');
export const GpsFixedIcon = createIcon(GpsFixedMui, 'GpsFixedIcon');
export const HistoryIcon = createIcon(HistoryMui, 'HistoryIcon');
export const ImageSearchIcon = createIcon(ImageSearchMui, 'ImageSearchIcon');
export const LinkIcon = createIcon(LinkMui, 'LinkIcon');
export const LocalParkingIcon = createIcon(LocalParkingMui, 'LocalParkingIcon');
export const MicIcon = createIcon(MicMui, 'MicIcon');
export const MoreVertIcon = createIcon(MoreVertMui, 'MoreVertIcon');
export const MoreHorizIcon = createIcon(MoreHorizMui, 'MoreHorizIcon');
export const OpenWithIcon = createIcon(OpenWithMui, 'OpenWithIcon');
export const PeopleIcon = createIcon(PeopleMui, 'PeopleIcon');
export const SettingsIcon = createIcon(SettingsMui, 'SettingsIcon');
export const StickyNote2Icon = createIcon(StickyNote2Mui, 'StickyNote2Icon');
export const TagIcon = createIcon(TagMui, 'TagIcon');
export const TrendingUpIcon = createIcon(TrendingUpMui, 'TrendingUpIcon');
export const TuneIcon = createIcon(TuneMui, 'TuneIcon');

// Re-export types
export type { IconProps, IconSize, IconColor } from './types';
export { sizeMap } from './types';

