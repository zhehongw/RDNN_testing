%% CLEAR 
clc;
clear;
close all;

%% READ DATA
net = ;

%% PARAMETERS

% type str
convStr = 'nnet.cnn.layer.Convolution2DLayer';
fcStr = 'nnet.cnn.layer.FullyConnectedLayer';

% count convolution and fc layers
countConv = 0;
countFc = 0;

%% (START)
fprintf('\n   *** STARTING SCRIPT %s *** \n', mfilename);

%% READ WEIGHTS AND DO CLUSTERING

fprintf('\n   *** READING DATA FROM MATLAB *** \n');
tic;
nLayers = length(net.Layers);
fprintf('       -- Elapsed time: %.2f s \n ', toc);

fprintf('\n   *** COUNTING CONV/FC LAYERS *** \n');
tic;
for i = 1: nLayers
    % if the layer is convLayer
    if isa(net.Layers(i), convStr)        
        countConv = countConv + 1;
    elseif isa(net.Layers(i), fcStr)
        countFc = countFc + 1;
    end
end
fprintf('       + Conv Layer: %d, Fc Layer: %d \n', countConv, countFc);
fprintf('       -- Elapsed time: %.2f s \n ', toc);

% store the indices and weights of the relevant layers
idxConv = zeros(countConv, 1);
idxFc = zeros(countFc, 1);

labelConv = cell(countConv, 1);
labelFc = cell(countFc, 1);

centerConv = cell(countConv, 1);
centerFc = cell(countFc, 1);

countConv = 0;
countFc   = 0;

fprintf('\n w2z   `2  wgzz*** CLUSTERING THE WEIGHTS *** \n');
tic;

for i = 1: nLayers          
     
     % if the layer is convLayer
    if isa(net.Layers(i), convStr)        
        fprintf('       + clustering Conv Layer [%d/%d] \n', countConv+1, length(idxConv));
        tic;
        countConv = countConv + 1;
        idxConv(countConv) = i;
        
        w_conv = net.Layers(i).Weights(:);
        
         
        figpath_conv = sprintf(['%d','conv.png'], countConv);
        [f,xi] = ksdensity(w_conv);
        figure
        plot(xi,f);
        saveas(gcf,figpath_conv); 
    

 elseif isa(net.Layers(i), fcStr)
        fprintf('       + clustering Fc Layer [%d/%d] \n', countFc+1, length(idxFc));
        tic;
        countFc = countFc + 1;
        idxFc(countFc) = i;
        
        w_fc = net.Layers(i).Weights(:);
        
        figpath_fc = sprintf(['%d','fc.png'], countFc);
        [f,xi] = ksdensity(w_fc);
        figure
        plot(xi,f);
        saveas(gcf,figpath_fc); 
    end
end
